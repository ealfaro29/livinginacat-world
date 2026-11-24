#pragma once
#include <stdint.h>
bool entity_panel_command(const char *suffix, uint8_t client);
void entity_screen_task();
void entity_flush_complete();
