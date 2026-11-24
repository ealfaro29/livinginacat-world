// SPDX-License-Identifier: GPL-3.0-or-later
#include "../Grbl.h"
#include "../mks/MKS_LVGL.h"
#include "device.h"
#include "panel.h"
#include <inttypes.h>
#include <algorithm>

// One writer (serial GRBL). Only the display task changes LVGL objects.
namespace {
constexpr size_t text_bytes = 96;
struct Frame {
    unsigned seq, ready, task, count, page;
    char title[text_bytes+1], action[text_bytes+1], rows[3][text_bytes+1];
};
Frame staging{}, current{};
unsigned fields, required;
bool assembling;
portMUX_TYPE guard = portMUX_INITIALIZER_UNLOCKED;
unsigned requested_page, drawn, view_code, touches, flushes;
unsigned presses, last_adc_x, last_adc_y, last_z, live_z;
int last_x, last_y;
uint32_t heartbeat;

// The ST7789V writes in mode 2. The XPT2046 samples in mode 0 on the same
// wires. Do not reuse TFT_eSPI's display-specific clock edge for touch reads.
uint16_t touch_channel(SPIClass &bus, uint8_t cmd) {
    uint16_t values[3];
    for (unsigned i=0;i<3;++i) {
        bus.transfer(cmd);
        uint16_t high=bus.transfer(0);
        values[i]=((high<<8)|bus.transfer(0))>>3;
    }
    if (values[0]>values[1]) std::swap(values[0],values[1]);
    if (values[1]>values[2]) std::swap(values[1],values[2]);
    return std::max(values[0],values[1]);
}
bool read_touch(uint16_t &x, uint16_t &y, uint16_t &z) {
    auto &bus=tft.getSPIinstance();
    bus.beginTransaction(SPISettings(1000000,MSBFIRST,SPI_MODE0));
    digitalWrite(TFT_CS,HIGH);
    digitalWrite(TOUCH_CS,LOW);
    z=touch_channel(bus,0xb0);
    bool down=z>30 && z<4095;
    if (down) {
        x=touch_channel(bus,0x90);
        y=touch_channel(bus,0xd0);
        down=x>30 && x<4065 && y>30 && y<4065 && touch_channel(bus,0xb0)>30;
    }
    digitalWrite(TOUCH_CS,HIGH);
    bus.endTransaction();
    return down;
}
bool received;
unsigned page_max(unsigned count) { return count ? (count-1)/3 : 0; }

int digit(char c) {
    if (c >= '0' && c <= '9') return c-'0';
    if (c >= 'A' && c <= 'F') return c-'A'+10;
    if (c >= 'a' && c <= 'f') return c-'a'+10;
    return -1;
}
bool decode(char *dest, const char *s) {
    size_t n = strlen(s);
    if (n % 2 || n > 2*text_bytes) return false;
    for (size_t i=0; i<n/2; ++i) {
        int a=digit(s[i*2]), b=digit(s[i*2+1]);
        if (a<0 || b<0 || (a*16+b)<32 || (a*16+b)==127) return false;
        dest[i]=char(a*16+b);
    }
    dest[n/2]=0;
    return true;
}
}

bool entity_panel_command(const char *s, uint8_t client) {
    if (!*s) {
        portENTER_CRITICAL(&guard);
        unsigned p=requested_page, seq=current.seq, render=drawn, v=view_code, t=touches, f=flushes;
        unsigned n=presses, ax=last_adc_x, ay=last_adc_y, z=last_z, live=live_z;
        int px=last_x,py=last_y;
        heartbeat=millis();
        portEXIT_CRITICAL(&guard);
        grbl_sendf(client, "[ENTITY:1,%u,%u,%u,%u,%u,%u]\r\n",p,seq,render,v,t,f);
        grbl_sendf(client, "[ENTITY:TOUCH,%u,%u,%u,%u,%d,%d,%u]\r\n",n,ax,ay,z,px,py,live);
        return true;
    }
    if (!strncmp(s,"=B,",3)) {
        Frame next{};
        int used=0;
        assembling=false;
        if (sscanf(s+3,"%u,%u,%u,%u,%u%n",&next.seq,&next.ready,&next.task,&next.count,&next.page,&used)!=5
            || s[3+used] || !next.seq || next.ready>1 || next.count>1000000 || next.page>page_max(next.count)) return false;
        staging=next;
        unsigned rows=next.count-next.page*3;
        required=(1u<<(2+(rows<3 ? rows:3)))-1;
        fields=0;
        assembling=true;
        return true;
    }
    if (!assembling) return false;
    if (!strncmp(s,"=E,",3)) {
        unsigned seq; int used=0;
        if (sscanf(s+3,"%u%n",&seq,&used)!=1 || s[3+used] || seq!=staging.seq ||
            fields!=required || (staging.task!=0)!=(staging.title[0]!=0)) return false;
        portENTER_CRITICAL(&guard);
        current=staging;
        received=true;
        heartbeat=millis();
        portEXIT_CRITICAL(&guard);
        assembling=false;
        return true;
    }
    if (strlen(s)<3 || s[0]!='=' || s[2]!=',') return false;
    unsigned i;
    char *out;
    if (s[1]=='T') {i=0;out=staging.title;}
    else if (s[1]=='A') {i=1;out=staging.action;}
    else if (s[1]>='0' && s[1]<='2') {i=s[1]-'0'+2;out=staging.rows[i-2];}
    else return false;
    if (!(required&(1u<<i)) || !decode(out,s+3)) return false;
    fields|=1u<<i;
    return true;
}
void entity_flush_complete() {
    portENTER_CRITICAL(&guard);
    ++flushes;
    portEXIT_CRITICAL(&guard);
}
void entity_screen_task() {
    mks_lvgl_init();
    lv_obj_t *root=lv_scr_act();
    EntityLanguage lang=ENTITY_ES;
    EntityView view=ENTITY_BOOT;
    entity_panel_draw(root,view,lang,nullptr,0);
    lv_refr_now(nullptr);
    LCD_BLK_ON;
    const uint32_t boot=millis();
    unsigned last_seq=0,page=0;
    bool was_online=false, was_running=false, pressed=false;
    uint32_t last_touch_poll=0;
    unsigned consistent=0;
    for (;;) {
        Frame next;
        const uint32_t now=millis();
        portENTER_CRITICAL(&guard);
        next=current;
        bool online=received && (millis()-heartbeat < 90000UL);
        portEXIT_CRITICAL(&guard);
        bool changed=false;
        if (view==ENTITY_BOOT && now-boot>=1000) {view=ENTITY_TASK;changed=true;}
        if (view!=ENTITY_BOOT) {
            bool running=online && next.task;
            if (running!=was_running || online!=was_online) {view=ENTITY_TASK;page=0;changed=true;}
            if (page>page_max(next.count)) {page=page_max(next.count);changed=true;}
            if (now-last_touch_poll>=25) {
                last_touch_poll=now;
                uint16_t adc90=0,adcd0=0,z=0;
                bool contact=read_touch(adc90,adcd0,z);
                consistent=contact ? std::min(consistent+1,2u) : 0;
                bool down=consistent>=2;
                portENTER_CRITICAL(&guard); live_z=z; portEXIT_CRITICAL(&guard);
                if (down && !pressed) {
                    // The TS24-R reference coefficients use 11-bit samples; the ADC above
                    // returns all 12 bits. Preserve the extra bit until the final shift.
                    int x=((int32_t(adc90)*-11606)>>17)+349;
                    int y=((int32_t(adcd0)*8556)>>17)-18;
                    portENTER_CRITICAL(&guard);
                    ++presses; last_adc_x=adc90; last_adc_y=adcd0; last_z=z; last_x=x; last_y=y;
                    portEXIT_CRITICAL(&guard);
                    auto hit=entity_panel_hit(view,x,y,page,next.count);
                    if (hit!=ENTITY_NO_TOUCH) {
                        if (hit==ENTITY_SWITCH_LANGUAGE) lang=lang==ENTITY_ES?ENTITY_EN:ENTITY_ES;
                        if (hit==ENTITY_SHOW_TASK) {view=ENTITY_TASK;page=0;}
                        if (hit==ENTITY_SHOW_QUEUE) {view=ENTITY_QUEUE;page=0;}
                        if (hit==ENTITY_PREVIOUS_PAGE) --page;
                        if (hit==ENTITY_NEXT_PAGE) ++page;
                        changed=true;
                        portENTER_CRITICAL(&guard); ++touches; portEXIT_CRITICAL(&guard);
                    }
                }
                pressed=down;
            }
            if (changed || last_seq!=next.seq) {
                const char *rows[]={next.rows[0],next.rows[1],next.rows[2]};
                EntityPanelState state{online, bool(next.ready), next.title, next.action, rows,
                                      next.count,next.page*3,3};
                entity_panel_draw(root,view,lang,&state,page);
                lv_refr_now(nullptr);
                portENTER_CRITICAL(&guard);
                drawn=next.seq;
                requested_page=page;
                view_code=view==ENTITY_QUEUE?3:!online?4:running?2:next.ready?1:5;
                portEXIT_CRITICAL(&guard);
                last_seq=next.seq;
                was_running=running;
                was_online=online;
            }
        }
        lv_task_handler();
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}
