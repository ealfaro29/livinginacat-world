#include "panel.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static lv_color_t framebuffer[240][320], strip[320*12];
static void flush(lv_disp_drv_t *drv, const lv_area_t *area, lv_color_t *pixels) {
 for (int y=area->y1;y<=area->y2;y++) for(int x=area->x1;x<=area->x2;x++) {
   if(x>=0 && x<320 && y>=0 && y<240) framebuffer[y][x]=*pixels;
   pixels++;
 }
 lv_disp_flush_ready(drv);
}
static void dump(const char *folder,const char *name) {
 char file[2048];snprintf(file,sizeof(file),"%s/%s.ppm",folder,name);
 FILE *f=fopen(file,"wb");assert(f);fputs("P6\n320 240\n255\n",f);
 lv_refr_now(NULL);
 for(int y=0;y<240;y++)for(int x=0;x<320;x++){
  lv_color32_t c={.full=lv_color_to32(framebuffer[y][x])};uint8_t rgb[]={c.ch.red,c.ch.green,c.ch.blue};fwrite(rgb,1,3,f);
 }fclose(f);
}
int main(int argc,char **argv){
 if(argc!=2)return 2;
 lv_init();
 static lv_disp_buf_t buf;
 lv_disp_buf_init(&buf,strip,NULL,320*12);
 lv_disp_drv_t drv; lv_disp_drv_init(&drv);drv.hor_res=320;drv.ver_res=240;drv.buffer=&buf;drv.flush_cb=flush;
 assert(lv_disp_drv_register(&drv));
 const char *queue[]={"Abrir el calendario","Check the time","Próxima tarea","Última"};
 EntityPanelState state={true,true,"Calcular 89 × 90","tap",queue,4};
 lv_obj_t *root=lv_scr_act();
 entity_panel_draw(root,ENTITY_BOOT,ENTITY_ES,&state,0);dump(argv[1],"boot");
 entity_panel_draw(root,ENTITY_TASK,ENTITY_ES,&state,0);dump(argv[1],"task");
 entity_panel_draw(root,ENTITY_QUEUE,ENTITY_EN,&state,0);dump(argv[1],"queue");
 entity_panel_draw(root,ENTITY_QUEUE,ENTITY_ES,&state,1);dump(argv[1],"page2");
 entity_panel_draw(root,ENTITY_TASK,ENTITY_EN,NULL,0);dump(argv[1],"offline");
 EntityPanelState idle={.online=true,.ready=true};
 EntityView selected=entity_panel_follow_task(ENTITY_QUEUE,&state,&idle);
 assert(selected==ENTITY_TASK);
 entity_panel_draw(root,selected,ENTITY_ES,&idle,0);dump(argv[1],"idle-es");
 int lit=0;
 for(int y=55;y<115;y++)for(int x=128;x<192;x++){
  lv_color32_t pixel={.full=lv_color_to32(framebuffer[y][x])};
  if(pixel.ch.red>=240 && pixel.ch.green>=245 && pixel.ch.blue<8)lit++;
 }
 assert(lit>1000);
 int white_wordmark=0;
 for(int y=122;y<162;y++)for(int x=60;x<260;x++){
  lv_color32_t pixel={.full=lv_color_to32(framebuffer[y][x])};
  if(pixel.ch.red>=240 && pixel.ch.green>=240 && pixel.ch.blue>=240)white_wordmark++;
 }
 assert(white_wordmark>100);
 assert(framebuffer[42][15].full==lv_color_hex(0x000000).full);
 entity_panel_draw(root,selected,ENTITY_EN,&idle,0);dump(argv[1],"idle-en");
 EntityPanelState waiting={.online=true,.ready=true,.queue_titles=queue,.queue_count=4};
 assert(entity_panel_follow_task(ENTITY_QUEUE,&idle,&waiting)==ENTITY_QUEUE);
 entity_panel_draw(root,ENTITY_TASK,ENTITY_ES,&waiting,0);dump(argv[1],"waiting");
 assert(entity_panel_follow_task(ENTITY_QUEUE,&waiting,&state)==ENTITY_TASK);
 const char *slice[]={"Última"};
 EntityPanelState paged={true,true,"Calcular 89 × 90","tap",slice,4,3,1};
 entity_panel_draw(root,ENTITY_QUEUE,ENTITY_ES,&paged,1);dump(argv[1],"sliced-page2");
 EntityPanelState setup={.online=true,.ready=false};
 entity_panel_draw(root,ENTITY_TASK,ENTITY_ES,&setup,0);dump(argv[1],"setup");
 assert(entity_panel_hit(ENTITY_BOOT,281,14,0,0)==ENTITY_NO_TOUCH);
 assert(entity_panel_hit(ENTITY_TASK,281,14,0,0)==ENTITY_SWITCH_LANGUAGE);
 assert(entity_panel_hit(ENTITY_TASK,204,221,0,0)==ENTITY_SHOW_QUEUE);
 assert(entity_panel_hit(ENTITY_QUEUE,280,60,0,4)==ENTITY_NEXT_PAGE);
 assert(entity_panel_hit(ENTITY_QUEUE,280,60,1,4)==ENTITY_NO_TOUCH);
 assert(entity_panel_hit(ENTITY_QUEUE,248,60,1,4)==ENTITY_PREVIOUS_PAGE);
 puts("Native 320x240: boot, idle ES/EN, task, queue, pagination, pending, setup, offline and touch transitions OK");
 return 0;
}
