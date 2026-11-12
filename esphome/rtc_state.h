#pragma once

#include <cstdint>

#include "esp_attr.h"

// RTC memory survives deep sleep but not a power loss or restart, when these all return to zero.
static RTC_DATA_ATTR uint32_t rtc_failed_wakes = 0;  // Wakes in a row without Home Assistant.
static RTC_DATA_ATTR bool rtc_low_battery = false;
static RTC_DATA_ATTR bool rtc_critical_battery = false;
static RTC_DATA_ATTR char rtc_last_data[256] = {0};    // Lets the device redraw while offline.
// The same, for the notice. Home Assistant limits a notice to 300 characters, at most 2 bytes each.
static RTC_DATA_ATTR char rtc_last_notice[704] = {0};
// Notice keys are short ids from Home Assistant, unique to each notice.
static RTC_DATA_ATTR char rtc_shown_notice[24] = {0};      // The notice on screen, which a long press dismisses.
static RTC_DATA_ATTR char rtc_dismissed_notice[24] = {0};  // The last one dismissed, reported to Home Assistant.
