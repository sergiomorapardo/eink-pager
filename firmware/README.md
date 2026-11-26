# Firmware (pendiente)

Hardware sugerido para empezar (~USD 30–40):

- **LILYGO T5 2.13"/2.9" o ESP32 + Waveshare 2.9" e-Paper (296×128, B/N)**.
- Batería LiPo pequeña; con refresco cada 1–2 min y deep sleep entre ciclos dura días.

Plan del firmware (PlatformIO + GxEPD2):

1. Conectarse al Wi‑Fi.
2. `GET http://<mac>:8787/frame.bmp` (1 bit, 296×128) y pintarlo tal cual.
   Toda la lógica vive en el servidor; el dispositivo es "tonto" a propósito.
3. Refresco parcial si cambió la imagen (comparar hash) y completo cada ~20 ciclos para
   limpiar el ghosting.
4. Deep sleep 60 s. Botón para refrescar al instante.

Para que el ESP32 alcance el servidor, arráncalo con `--host 0.0.0.0`.
