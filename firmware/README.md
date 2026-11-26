# Firmware (planned)

Suggested starter hardware (~USD 30–40):

- **LILYGO T5 2.13"/2.9" or ESP32 + Waveshare 2.9" e-Paper (296×128, B/W)**.
- Small LiPo battery; refreshing every 1–2 min with deep sleep between cycles lasts days.

Firmware plan (PlatformIO + GxEPD2):

1. Connect to Wi-Fi.
2. `GET http://<mac>:8787/frame.bmp` (1-bit, 296×128) and draw it as-is.
   All logic lives on the server; the device is intentionally "dumb".
3. Partial refresh when the image changed (compare hashes), full refresh every ~20 cycles
   to clear ghosting.
4. Deep sleep 60 s. Button for an immediate refresh.

Start the server with `--host 0.0.0.0` so the ESP32 can reach it.
