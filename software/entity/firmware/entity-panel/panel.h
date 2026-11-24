#ifndef ENTITY_PANEL_H
#define ENTITY_PANEL_H
#include "lvgl.h"
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum { ENTITY_BOOT, ENTITY_TASK, ENTITY_QUEUE } EntityView;
typedef enum { ENTITY_ES, ENTITY_EN } EntityLanguage;
typedef enum {
    ENTITY_NO_TOUCH, ENTITY_SHOW_TASK, ENTITY_SHOW_QUEUE, ENTITY_SWITCH_LANGUAGE,
    ENTITY_PREVIOUS_PAGE, ENTITY_NEXT_PAGE
} EntityTouch;

/* Read-only state supplied by the host. Titles stay in the operator's language.
 * The array is either the full queue or the page beginning at queue_first. All pointers are borrowed for this draw. */
typedef struct {
    bool online;
    bool ready;
    const char *current_title;
    const char *action; /* MCP action name, e.g. "tap", or NULL */
    const char *const *queue_titles;
    size_t queue_count;
    size_t queue_first;
    size_t queue_supplied; /* Zero for a full, unsliced array. */
} EntityPanelState;

/* Use a dedicated 320 x 240 parent. Draw on the LVGL thread when state changes. */
void entity_panel_draw(lv_obj_t *parent, EntityView view, EntityLanguage lang,
                       const EntityPanelState *state, size_t page);
/* Follow task starts and finishes. Preserve a manually selected queue between transitions. */
EntityView entity_panel_follow_task(EntityView selected, const EntityPanelState *previous,
                                    const EntityPanelState *next);
EntityTouch entity_panel_hit(EntityView view, int x, int y, size_t page, size_t queue_count);

#ifdef __cplusplus
}
#endif
#endif
