# Home Assistant weather display for the Zectrix Note 4C

ESPHome firmware that turns the [Zectrix Note 4C](https://wiki.zectrix.com/en/hardware/note4c/quick-start) into a battery-powered weather display. It shows an outdoor temperature and an hourly forecast from Home Assistant, on a 4.2" black, white, red and yellow e-paper panel.

| Day | Night |
|---|---|
| ![Daytime screen](docs/preview-day.png) | ![Night screen](docs/preview-night.png) |

These are generated previews with sample data. On the real panel, the inks are more muted and the text may differ slightly.

**Status:** a working personal project, shared as is. Battery life hasn't been measured yet. See [Known limitations](#known-limitations).

## How it works

1. In Home Assistant, an automation runs every 10 minutes and writes a compact summary of the temperature and forecast to a text helper.
2. The device wakes every 15 minutes, connects to Home Assistant and reads the helper.
3. If the value changed, the device redraws, which takes about 20 seconds. Then it goes back to sleep.

The device only reads the helper, so it doesn't need permission to perform actions in Home Assistant. All the forecast logic stays in Home Assistant, where it's easy to change without rebuilding firmware.

## What you need

- A Zectrix Note 4C. This firmware won't work on the black-and-white Note 4, which has a different panel.
- Home Assistant with a weather entity that provides hourly forecasts, and the ESPHome integration.
- [ESPHome](https://esphome.io/) 2026.10 or newer, either the CLI or the Device Builder add-on.
- A 2.4 GHz Wi-Fi network.

## Setup

### 1. Back up the factory firmware

Flashing replaces the factory firmware, so save the whole flash first. Keep the file private: it can contain data from your device.

```bash
pip install esptool
```

```bash
python -m esptool --chip esp32s3 --port COM3 --baud 460800 read-flash 0x0 0x1000000 note4c-factory.bin
```

Replace `COM3` with your device's port.

### 2. Set up Home Assistant

Copy [homeassistant/note4c_screen.yaml](homeassistant/note4c_screen.yaml) into your [packages](https://www.home-assistant.io/docs/configuration/packages/) folder and change the two entity IDs at the top to your own. Restart Home Assistant, then check that `input_text.note4c_screen` fills with data.

You can also create the helper and automation in the UI, using the same values.

### 3. Configure the firmware

Copy [esphome/secrets.example.yaml](esphome/secrets.example.yaml) to `esphome/secrets.yaml` and fill it in. If you use Device Builder, add these values to its Secrets instead.

The settings at the top of [esphome/note4c.yaml](esphome/note4c.yaml) cover the wake interval, the label above the temperature, and the helper's name. Screen text is in Polish. To change the language, edit `text_for` and the `"teraz"` label in the same file, and add any new letters to the fonts' `glyphs`.

### 4. Flash over USB

```bash
esphome run esphome/note4c.yaml --device COM3
```

If the port isn't detected, enter download mode: hold the round BOOT button, press the RESET pinhole once, then release BOOT.

### 5. Add it to Home Assistant

Add the ESPHome integration using the device's IP address and the API key from your secrets. Most wakes are short, so press BOOT first: it keeps the device awake for 3 minutes.

## Buttons

| Button | What it does |
|---|---|
| **BOOT** (round, front) | Wakes the device, reads fresh data, and keeps it awake for 3 minutes |
| **RESET** (pinhole) | Restarts the device, also with the 3-minute window |
| **UP, DOWN** | Not used |

## Updating over Wi-Fi

Press **BOOT**, then press **Install** in Device Builder, or run `esphome run` with the device's IP address, within 3 minutes.

Waking the device first matters. With mDNS on, Device Builder keeps showing the sleeping device as online, so Install tries to send straight away and usually fails.

If an update crashes on boot, the bootloader returns to the previous firmware. New firmware is only confirmed once Home Assistant has connected and the wake cycle has reached that point.

## Known limitations

- **Battery life isn't measured**, and the firmware doesn't report battery level yet. The hourly strip means a redraw most hours.
- **Possible crash on sleep:** an early test build crashed once in `mdns_free` when entering deep sleep. mDNS is needed for Device Builder to find the device. The crash hasn't been seen in testing since, but that testing was brief, and it hasn't been run for long at the final 15-minute interval.
- **Stale data isn't flagged:** if Home Assistant or the automation stops, the screen keeps showing the last values.
- **Slow refresh:** the panel only does full refreshes of about 20 seconds, with visible flashing. That's normal for four-colour e-paper.

## Changing the art

The art is drawn by Python scripts in [design/](design), using halftone dots to get extra tones from four inks. Run them with Pillow and requests installed:

```bash
python design/art.py
```

```bash
python design/preview.py
```

`art.py` writes the images that get built into the firmware to `esphome/art/`. To send them to Device Builder, create a bundle with `esphome bundle esphome/note4c.yaml` and import it. The bundle includes the secrets the config uses, so don't share it.

![All the weather art](docs/art-sheet.png)

## Credits and licence

MIT licensed. See [LICENSE](LICENSE). The panel's init sequence and pin mapping come from the MIT-licensed [reference firmware](https://github.com/LazyYoun/youn-ink-fourcolor-firmware): see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

This is an independent project, not affiliated with or endorsed by Zectrix.
