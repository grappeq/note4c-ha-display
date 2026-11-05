#pragma once

#include <cstdint>

#include "esp_attr.h"

// RTC memory survives deep sleep but not a power loss or restart, when these all return to zero.
static RTC_DATA_ATTR uint32_t rtc_failed_wakes = 0;  // Wakes in a row without Home Assistant.
static RTC_DATA_ATTR bool rtc_low_battery = false;
static RTC_DATA_ATTR char rtc_last_data[256] = {0};  // Lets the device redraw while offline.
