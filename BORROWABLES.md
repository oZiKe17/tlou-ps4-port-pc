# Funciones borrowables (TLOU) — ya implementadas en otros ports

Extraídas de `runtime_gr2.c`, `runtime_gr2_np.c`, `runtime_infamous.c` (GR2/ISS).
Copiar a `port/src/runtime_tlou.c` (o promover a `ps4_core` si un segundo port las necesita).

| # | Función | Biblioteca | Origen (port/archivo) | Tipo |
|---|---|---|---|---|
| 1 | accept | libkernel | GR2: runtime_gr2.c | real |
| 2 | bind | libkernel | GR2: runtime_gr2.c | real |
| 3 | listen | libkernel | GR2: runtime_gr2.c | real |
| 4 | recv | libkernel | GR2: runtime_gr2.c | real |
| 5 | select | libkernel | GR2: runtime_gr2.c | real |
| 6 | send | libkernel | GR2: runtime_gr2.c | real |
| 7 | shutdown | libkernel | GR2: runtime_gr2.c | real |
| 8 | socket | libkernel | GR2: runtime_gr2.c | real |
| 9 | sceKernelLoadStartModule | libkernel | GR2: runtime_gr2.c | real |
| 10 | sceFiberFinalize | libSceFiber | GR2: runtime_gr2.c | real |
| 11 | sceFiberReturnToThread | libSceFiber | GR2: runtime_gr2.c | real |
| 12 | sceFiberRun | libSceFiber | GR2: runtime_gr2.c | real |
| 13 | sceFiberSwitch | libSceFiber | GR2: runtime_gr2.c | real |
| 14 | _sceFiberInitializeImpl | libSceFiber | GR2: runtime_gr2.c | real |
| 15 | sceHttpGetAllResponseHeaders | libSceHttp | GR2: runtime_gr2_np.c | real |
| 16 | sceHttpParseResponseHeader | libSceHttp | GR2: runtime_gr2_np.c | real |
| 17 | sceHttpsSetSslCallback | libSceHttp | GR2: runtime_gr2_np.c | stub |
| 18 | sceJpegDecCreate | libSceJpegDec | GR2: runtime_gr2.c | real |
| 19 | sceJpegDecDecode | libSceJpegDec | GR2: runtime_gr2.c | real |
| 20 | sceJpegDecDelete | libSceJpegDec | GR2: runtime_gr2.c | real |
| 21 | sceJpegDecParseHeader | libSceJpegDec | GR2: runtime_gr2.c | real |
| 22 | sceJpegDecQueryMemorySize | libSceJpegDec | GR2: runtime_gr2.c | real |
| 23 | sceJpegEncCreate | libSceJpegEnc | GR2: runtime_gr2.c | real |
| 24 | sceJpegEncDelete | libSceJpegEnc | GR2: runtime_gr2.c | real |
| 25 | sceJpegEncEncode | libSceJpegEnc | GR2: runtime_gr2.c | real |
| 26 | sceJpegEncQueryMemorySize | libSceJpegEnc | GR2: runtime_gr2.c | real |
| 27 | sceNetGetpeername | libSceNet | GR2: runtime_gr2_np.c | stub |
| 28 | sceNetCtlInit | libSceNetCtl | ISS: runtime_infamous.c | real |
| 29 | sceNpCreateRequest | libSceNpManager | GR2: runtime_gr2_np.c | real |
| 30 | sceNpGetAccountCountry | libSceNpManager | GR2: runtime_gr2_np.c | real |
| 31 | scePlayGoGetEta | libScePlayGo | ISS: runtime_infamous.c | real |
| 32 | scePlayGoGetToDoList | libScePlayGo | ISS: runtime_infamous.c | real |
| 33 | scePlayGoSetLanguageMask | libScePlayGo | ISS: runtime_infamous.c | stub |
| 34 | scePngDecCreate | libScePngDec | GR2: runtime_gr2.c | real |
| 35 | scePngDecDecode | libScePngDec | GR2: runtime_gr2.c | real |
| 36 | scePngDecDelete | libScePngDec | GR2: runtime_gr2.c | real |
| 37 | scePngDecParseHeader | libScePngDec | GR2: runtime_gr2.c | real |
| 38 | scePngDecQueryMemorySize | libScePngDec | GR2: runtime_gr2.c | real |

Notas:
- Los stubs (sceHttpsSetSslCallback, sceNetGetpeername, scePlayGoSetLanguageMask) devuelven valor fijo; suficiente para offline.
- Los "real" son implementaciones funcionales; copiar tal cual y ajustar includes.
- En ISS los archivos son copias de GR2 (`runtime_gr2.c`/`runtime_gr2_np.c`); usar GR2 como fuente canónica.
- Promover a `ps4_core` cuando un segundo port (TLOU) las use: así evitamos duplicación.
