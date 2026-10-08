# RainLoopWeather FAST V1.1

V1.1 uses Smart Fast Brightness: it encodes only the brightness variants needed for the short source loop, caches them, then concatenates them with video stream-copy for the 8–12 hour output. Rain/wave/original audio remain time-varying.

Auto encoder runtime order: NVIDIA NVENC -> Intel QSV -> AMD AMF -> libx264. A failed/old NVIDIA driver no longer forces the whole 8–12h render onto CPU.

Source package: RainLoopWeatherFast_Source_V1.1.zip
