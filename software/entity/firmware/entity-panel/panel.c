#include "panel.h"
#include <stdio.h>
#include <string.h>

LV_FONT_DECLARE(entity_font)
LV_FONT_DECLARE(entity_wordmark_font)
extern const lv_img_dsc_t entity_mark;

static lv_style_t dark, lime, ink, muted, accent, rule, wordmark;

static void styles(void) {
    static bool initialized;
    if (initialized) return;
    lv_style_copy(&dark, &lv_style_plain);
    dark.body.main_color = dark.body.grad_color = lv_color_hex(0x000000);
    dark.body.radius = 0;
    dark.body.border.width = 0;
    dark.body.opa = LV_OPA_COVER;
    lv_style_copy(&lime, &dark);
    lime.body.main_color = lime.body.grad_color = lv_color_hex(0xf8ff00);
    lv_style_copy(&rule, &dark);
    rule.body.main_color = rule.body.grad_color = lv_color_hex(0x3c3c3c);
    lv_style_copy(&ink, &lv_style_plain);
    ink.text.font = &entity_font;
    ink.text.color = lv_color_hex(0xffffff);
    lv_style_copy(&muted, &ink);
    muted.text.color = lv_color_hex(0xdadada);
    lv_style_copy(&accent, &ink);
    accent.text.color = accent.image.color = lv_color_hex(0xf8ff00);
    /* LVGL 6 caches alpha-only artwork by source. Apply each view's tint at draw time. */
    accent.image.intense = LV_OPA_COVER;
    lv_style_copy(&wordmark, &ink);
    wordmark.text.font = &entity_wordmark_font;
    initialized = true;
}

static lv_obj_t *label(lv_obj_t *parent, int x, int y, int w, int h,
                       const char *text, lv_style_t *style, bool centered) {
    lv_obj_t *obj = lv_label_create(parent, NULL);
    lv_label_set_style(obj, LV_LABEL_STYLE_MAIN, style);
    lv_label_set_long_mode(obj, LV_LABEL_LONG_DOT);
    lv_obj_set_size(obj, w, h);
    lv_label_set_text(obj, text ? text : "");
    if (centered) lv_label_set_align(obj, LV_LABEL_ALIGN_CENTER);
    lv_obj_set_pos(obj, x, y);
    return obj;
}

static void line(lv_obj_t *parent, int x, int y, int w, int h, lv_style_t *style) {
    lv_obj_t *obj = lv_obj_create(parent, NULL);
    lv_obj_set_style(obj, style);
    lv_obj_set_size(obj, w, h);
    lv_obj_set_pos(obj, x, y);
}

static void sentient_mark(lv_obj_t *parent, int y, lv_style_t *style) {
    lv_obj_t *mark = lv_img_create(parent, NULL);
    lv_img_set_style(mark, LV_IMG_STYLE_MAIN, style);
    lv_img_set_src(mark, &entity_mark);
    lv_obj_set_pos(mark, (320 - entity_mark.header.w) / 2, y);
}

static bool has_task(const EntityPanelState *state) {
    return state && state->online && state->current_title && state->current_title[0];
}

EntityView entity_panel_follow_task(EntityView selected, const EntityPanelState *previous,
                                    const EntityPanelState *next) {
    if (selected == ENTITY_QUEUE && previous && previous->online && next && next->online &&
        has_task(previous) != has_task(next)) return ENTITY_TASK;
    return selected;
}

static const char *action_name(const char *action, EntityLanguage lang) {
    static const struct { const char *id, *es, *en; } actions[] = {
        {"tap","Toque en pantalla","Tapping the screen"}, {"double_tap","Toque doble","Double tap"},
        {"long_press","Pulsación larga","Long press"}, {"swipe","Deslizando","Swiping"},
        {"peek","Observando la pantalla","Observing screen"}, {"screenshot","Tomando una captura","Taking a screenshot"},
        {"home_screen","Abriendo el inicio","Opening Home Screen"}, {"go_back","Volviendo atrás","Going back"},
        {"force_quit","Cerrando la aplicación","Closing app"}, {"unlock_phone","Desbloqueando","Unlocking"},
        {"send_to_clipboard","Preparando el portapapeles","Preparing clipboard"}, {"sequence","Ejecutando una secuencia","Running a sequence"}
    };
    for (size_t i = 0; action && i < sizeof(actions)/sizeof(actions[0]); i++)
        if (strcmp(action, actions[i].id) == 0) return lang == ENTITY_ES ? actions[i].es : actions[i].en;
    return lang == ENTITY_ES ? "En curso" : "In progress";
}

void entity_panel_draw(lv_obj_t *parent, EntityView view, EntityLanguage lang,
                       const EntityPanelState *state, size_t page) {
    const bool es = lang == ENTITY_ES;
    const bool online = state && state->online;
    const size_t count = online ? state->queue_count : 0;
    const size_t pages = count ? 1 + (count - 1) / 3 : 1;
    char text[64];
    styles();
    lv_obj_clean(parent);
    lv_obj_set_style(parent, &dark);
    if (view == ENTITY_BOOT) {
        sentient_mark(parent, 57, &accent);
        label(parent, 24, 132, 272, 25, "Entity", &ink, true);
        label(parent, 24, 158, 272, 25, "by Sentient", &ink, true);
        return;
    }
    const bool running = has_task(state);
    const bool resting = view == ENTITY_TASK && !running;
    const char *status = !online ? (es ? "Sin conexión" : "Offline") :
        state->ready ? (es ? "Listo" : "Ready") : (es ? "Falta calibrar" : "Setup required");
    if (resting) {
        line(parent, 15, 20, 5, 5, online && state->ready ? &lime : &rule);
        label(parent, 27, 10, 225, 25, online && state->ready ? (es ? "En espera" : "Idle") : status, &muted, false);
    } else {
        label(parent, 12, 10, 65, 25, "Entity", &ink, false);
        label(parent, 92, 10, 174, 25, status, &muted, true);
    }
    label(parent, 270, 10, 46, 25, es ? "EN" : "ES", &accent, true);
    line(parent, 12, 39, 296, 1, &rule);
    if (resting) {
        sentient_mark(parent, 55, &accent);
        label(parent, 12, 122, 296, 40, "Entity", &wordmark, true);
        label(parent, 12, 165, 296, 24, "by Sentient", &muted, true);
    } else if (view == ENTITY_TASK) {
        label(parent, 15, 54, 290, 24, running ? (es ? "TAREA ACTUAL" : "CURRENT TASK") : (es ? "ESTADO" : "STATUS"), &muted, false);
        const char *title = running ? state->current_title : status;
        label(parent, 15, 85, 290, 63, title, &ink, false);
        const char *activity = !online ? (es ? "Esperando conexión" : "Waiting for connection") :
            running ? action_name(state->action, lang) : count ? (es ? "Esperando tu orden" : "Waiting for your command") : (es ? "Sin tareas pendientes" : "No pending tasks");
        label(parent, 15, running && count ? 143 : 167, 290, 24, activity, &muted, false);
        if (running && count && state->queue_titles && !state->queue_first) {
            label(parent, 15, 170, 97, 24, es ? "Siguiente" : "Next", &accent, false);
            label(parent, 112, 170, 193, 24, state->queue_titles[0], &ink, false);
        }
    } else {
        if (page >= pages) page = pages - 1;
        if (pages > 1) snprintf(text, sizeof(text), "%s %zu/%zu", es ? "EN COLA" : "IN QUEUE", page+1, pages);
        else snprintf(text, sizeof(text), "%s", es ? "EN COLA" : "IN QUEUE");
        label(parent, 15, 52, 209, 24, text, &muted, false);
        if (pages > 1) {
            label(parent, 229, 51, 38, 25, "<", page ? &accent : &muted, true);
            label(parent, 275, 51, 38, 25, ">", page+1 < pages ? &accent : &muted, true);
        }
        if (!count) label(parent, 15, 97, 290, 45, online ? (es ? "La cola está vacía." : "The queue is empty.") : (es ? "Esperando conexión." : "Waiting for connection."), &ink, false);
        for (size_t i=0; state && state->queue_titles && i<3 && page*3+i<count; i++) {
            size_t index=page*3+i;
            if (index < state->queue_first || (state->queue_supplied &&
                index-state->queue_first >= state->queue_supplied)) continue;
            int y=85+(int)i*34;
            snprintf(text,sizeof(text),"%zu",index+1);
            label(parent,15,y,40,24,text,&accent,false);
            label(parent,59,y,247,24,state->queue_titles[index-state->queue_first],&ink,false);
            line(parent,15,y+26,290,1,&rule);
        }
    }
    line(parent, 0, 197, 320, 1, &rule);
    label(parent, 0, 207, 160, 25, es ? "Tarea" : "Task", view == ENTITY_TASK ? &accent : &muted, true);
    if (online) snprintf(text, sizeof(text), "%s  %zu", es ? "Cola" : "Queue", count);
    else snprintf(text, sizeof(text), "%s  -", es ? "Cola" : "Queue");
    label(parent, 160, 207, 160, 25, text, view == ENTITY_QUEUE ? &accent : &muted, true);
    line(parent, view == ENTITY_TASK ? 0 : 160, 237, 160, 3, &lime);
}

EntityTouch entity_panel_hit(EntityView view, int x, int y, size_t page, size_t count) {
    if (view == ENTITY_BOOT || x<0 || x>=320 || y<0 || y>=240) return ENTITY_NO_TOUCH;
    if (y>=198) return x<160 ? ENTITY_SHOW_TASK : ENTITY_SHOW_QUEUE;
    if (y<40 && x>=267) return ENTITY_SWITCH_LANGUAGE;
    if (view == ENTITY_QUEUE && y>=43 && y<82 && count>3) {
        if (x>=225 && x<272 && page>0) return ENTITY_PREVIOUS_PAGE;
        if (x>=272 && page<(count-1)/3) return ENTITY_NEXT_PAGE;
    }
    return ENTITY_NO_TOUCH;
}
