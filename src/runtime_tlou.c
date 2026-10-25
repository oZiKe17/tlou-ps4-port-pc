/* runtime_tlou.c — stubs para importaciones faltantes de TLOU (CUSA00552).
 * Firmas refinadas con shadPS4 + POSIX + aerolib names. */

#include "runtime.h"
#include <stdio.h>
#include <string.h>

/* k1SwgkMSOM8#libSceRemoteplay -> sceRemoteplayInitialize */
int sceRemoteplayInitialize(void) { return 0; }

/* BOwybKVa3Do#libSceRemoteplay -> sceRemoteplayTerminate */
int sceRemoteplayTerminate(void) { return 0; }

/* 0Cq8ipKr9n0#libkernel -> sceKernelUtimes */
int sceKernelUtimes(char*, void*) { return 0; }

/* DHmwsa6S8Tc#libSceNpCommerce -> sceNpCommerceShowPsStoreIcon */
int sceNpCommerceShowPsStoreIcon(int) { return 0; }

/* dsqCVsNM0Zg#libSceNpCommerce -> sceNpCommerceHidePsStoreIcon */
int sceNpCommerceHidePsStoreIcon(void) { return 0; }

/* -Q1-u1a7p0g#libScePlayGo -> scePlayGoPrefetch */
int scePlayGoPrefetch(void*, void*, unsigned, void*) { return 0; }

/* 3OMbYZBaa50#libScePlayGo -> scePlayGoGetLanguageMask */
int scePlayGoGetLanguageMask(void*, void*) { return 0; }

/* Gl6w5i0JokY#libSceAppContent -> sceAppContentDownloadDataGetAvailableSpaceKb */
int sceAppContentDownloadDataGetAvailableSpaceKb(void*, void*) { return 0; }

/* uvT2iYBBnkY#libkernel -> sceKernelSync */
void sceKernelSync(void) { }

/* Dbbkj6YHWdo#libSceCoredump -> sceCoredumpWriteUserData */
int sceCoredumpWriteUserData(void) { return 0; }

/* 8zLSfEfW5AU#libSceCoredump -> sceCoredumpRegisterCoredumpHandler */
int sceCoredumpRegisterCoredumpHandler(void*, unsigned long, void*) { return 0; }

/* -LJbF9b-Who#libSceNpSns -> sceNpSnsFacebookAbortRequest */
int sceNpSnsFacebookAbortRequest(void) { return 0; }

/* iQr9UxPHUFs#libSceNpUtility -> sceNpLookupCreateRequest */
int sceNpLookupCreateRequest(void*) { return 0; }

/* cdqOFyupRS4#libSceNpSnsFacebookDialog -> sceNpSnsFacebookDialogTerminate */
int sceNpSnsFacebookDialogTerminate(void) { return 0; }

/* OoTjfxl8-wI#libSceNpSns -> sceNpSnsFacebookCreateRequest */
int sceNpSnsFacebookCreateRequest(void) { return 0; }

/* VtyS8XLBqNE#libSceNpSns -> sceNpSnsFacebookGetAccessToken */
int sceNpSnsFacebookGetAccessToken(void) { return 0; }

/* pTvAKV1iQkE#libSceNpSns -> sceNpSnsFacebookDeleteRequest */
int sceNpSnsFacebookDeleteRequest(void) { return 0; }

/* tdQArULbNQk#libSceNpSnsFacebookDialog -> sceNpSnsFacebookDialogInitialize */
int sceNpSnsFacebookDialogInitialize(void) { return 0; }

/* Hi3onqHSN6M#libSceNpSnsFacebookDialog -> sceNpSnsFacebookDialogOpen */
int sceNpSnsFacebookDialogOpen(void) { return 0; }

/* fjV7C8H0Y8k#libSceNpSnsFacebookDialog -> sceNpSnsFacebookDialogUpdateStatus */
int sceNpSnsFacebookDialogUpdateStatus(void) { return 0; }

/* AifdcI1aKas#libSceNpSnsFacebookDialog -> sceNpSnsFacebookDialogGetResult */
int sceNpSnsFacebookDialogGetResult(void) { return 0; }

/* zNGh-zoQTD0#libSceHttp -> sceHttpRemoveRequestHeader */
int sceHttpRemoveRequestHeader(int, char*) { return 0; }

/* 5LZA+KPISVA#libSceHttp -> sceHttpUriBuild */
int sceHttpUriBuild(char*, void*, unsigned long, void*, unsigned) { return 0; }

/* IWalAn-guFs#libSceHttp -> sceHttpUriParse */
int sceHttpUriParse(void*, char*, void*, void*, unsigned long) { return 0; }

/* NxEI1KByvCI#libSceRtc -> sceRtcParseDateTime */
int sceRtcParseDateTime(void*, char*) { return 0; }

/* QBFoAIjJoXQ#libSceVoice -> sceVoiceSetVolume */
int sceVoiceSetVolume(unsigned, float) { return 0; }

/* jjkCjneOYSs#libSceVoice -> sceVoiceGetVolume */
int sceVoiceGetVolume(unsigned, void*) { return 0; }

/* oUha0S-Ij9Q#libSceVoice -> sceVoiceSetMuteFlagAll */
int sceVoiceSetMuteFlagAll(int) { return 0; }

/* gwUynkEgNFY#libSceVoice -> sceVoiceSetMuteFlag */
int sceVoiceSetMuteFlag(unsigned, int) { return 0; }

/* Pc4z1QjForU#libSceVoice -> sceVoiceGetMuteFlag */
int sceVoiceGetMuteFlag(unsigned, void*) { return 0; }

/* 2HajCEGgG4s#libSceNpSignaling -> sceNpSignalingGetPeerNetInfoResult */
int sceNpSignalingGetPeerNetInfoResult(void*, void*, void*) { return 0; }

/* AN3h0EBSX7A#libSceNpSignaling -> sceNpSignalingGetConnectionInfo */
int sceNpSignalingGetConnectionInfo(void*, void*, int, void*) { return 0; }

/* b4qaXPzMJxo#libSceNpSignaling -> sceNpSignalingTerminateConnection */
int sceNpSignalingTerminateConnection(void*, void*) { return 0; }

/* GQ0hqmzj0F4#libSceNpSignaling -> sceNpSignalingGetConnectionFromNpId */
int sceNpSignalingGetConnectionFromNpId(void*, void*, void*) { return 0; }

/* BdykpTwq2bs#libSceNpManager -> sceNpInGameMessageAbortHandle */
int sceNpInGameMessageAbortHandle(void) { return 0; }

/* cE7wIsqXdZ8#libSceNpAuth -> sceNpAuthAbortRequest */
int sceNpAuthAbortRequest(int) { return 0; }

/* GFhVUpRmbHE#libSceNpManager -> sceNpInGameMessageInitialize */
int sceNpInGameMessageInitialize(void) { return 0; }

/* s4UEa5iBJdc#libSceNpManager -> sceNpInGameMessageCreateHandle */
int sceNpInGameMessageCreateHandle(void) { return 0; }

/* Vh1bhUG6mSs#libSceNpManager -> sceNpInGameMessagePrepare */
int sceNpInGameMessagePrepare(void) { return 0; }

/* bMG3cVmUmuk#libSceNpManager -> sceNpInGameMessageTerminate */
int sceNpInGameMessageTerminate(void) { return 0; }

/* 6bwFkosYRQg#libSceNpAuth -> sceNpAuthCreateRequest */
int sceNpAuthCreateRequest(void) { return 0; }

/* ON7Sf5XEMmI#libSceNpManager -> sceNpInGameMessageSendData */
int sceNpInGameMessageSendData(void) { return 0; }

/* 4n51s0zEf0c#libScePosix -> inet_pton */
int inet_pton(int, const char*, void*) { return 0; }

/* 7gxh+5QubhY#libSceAppContent -> sceAppContentAddcontEnqueueDownload */
int sceAppContentAddcontEnqueueDownload(void) { return 0; }

/* VANhIWcqYak#libSceAppContent -> sceAppContentAddcontMount */
int sceAppContentAddcontMount(unsigned, void*, void*) { return 0; }

/* g3PNjYKWqnQ#libSceRemoteplay -> sceRemoteplayGetConnectionStatus */
int sceRemoteplayGetConnectionStatus(void*, void*) { return 0; }

/* PMVehSlfZ94#libSceIme -> sceImeKeyboardClose */
int sceImeKeyboardClose(void*) { return 0; }

/* eaFXjfJv3xs#libSceIme -> sceImeKeyboardOpen */
int sceImeKeyboardOpen(void*, void*) { return 0; }

/* dKadqZFgKKQ#libSceIme -> sceImeKeyboardGetResourceId */
int sceImeKeyboardGetResourceId(void*, void*) { return 0; }

/* -4GCfYdNF1s#libSceIme -> sceImeUpdate */
int sceImeUpdate(void*) { return 0; }

/* IuxnUuXk6Bg#libkernel -> sceKernelGetModuleList */
int sceKernelGetModuleList(void*, unsigned long, void*) { return 0; }

/* kUpgrXIrz7Q#libkernel -> sceKernelGetModuleInfo */
int sceKernelGetModuleInfo(int, void*) { return 0; }

/* 79M-JqvvGo0#libSceNpWebApi -> sceNpWebApiCreateHandle */
int sceNpWebApiCreateHandle(int) { return 0; }

/* sIFx734+xys#libSceNpWebApi -> sceNpWebApiCreateServicePushEventFilter */
int sceNpWebApiCreateServicePushEventFilter(int, int, char*, void*, void*, unsigned long) { return 0; }

/* kJQJE0uKm5w#libSceNpWebApi -> sceNpWebApiRegisterServicePushEventCallback */
int sceNpWebApiRegisterServicePushEventCallback(int, int, void*, void*) { return 0; }

/* PfQ+f6ws764#libSceNpWebApi -> sceNpWebApiDeleteServicePushEventFilter */
int sceNpWebApiDeleteServicePushEventFilter(int, int) { return 0; }

/* B6HVJtDYxEE#libSceInvitationDialog -> sceInvitationDialogTerminate */
int sceInvitationDialogTerminate(void) { return 0; }

/* XvA5KS56wcs#libSceInvitationDialog -> sceInvitationDialogInitialize */
int sceInvitationDialogInitialize(void) { return 0; }

/* 0zU0G+wiVLA#libSceInvitationDialog -> sceInvitationDialogOpen */
int sceInvitationDialogOpen(void*) { return 0; }

/* 9+g9iOq+7kg#libSceInvitationDialog -> sceInvitationDialogUpdateStatus */
int sceInvitationDialogUpdateStatus(void) { return 0; }

/* 8XKR6wa64iQ#libSceInvitationDialog -> sceInvitationDialogGetResult */
int sceInvitationDialogGetResult(void*) { return 0; }

/* DGMG3JshrZU#libkernel -> sceKernelSetVirtualRangeName */
int sceKernelSetVirtualRangeName(void*, unsigned long, char*) { return 0; }

/* asjUJJ+aa8s#libSceFiber -> sceFiberOptParamInitialize */
int sceFiberOptParamInitialize(void*) { return 0; }

/* uq2Y5BFz0PE#libSceFiber -> sceFiberGetInfo */
int sceFiberGetInfo(void*, void*) { return 0; }

/* JzyT91ucGDc#libSceFiber -> sceFiberRename */
int sceFiberRename(void*, char*) { return 0; }

/* fFxGkxF2bVo#libScePosix -> setsockopt */
int setsockopt(int, int, int, const void*, unsigned) { return 0; }

/* 6O8EwYOgH9Y#libScePosix -> getsockopt */
int getsockopt(int, int, int, void*, unsigned*) { return 0; }

/* oBr313PppNE#libScePosix -> sendto */
long sendto(int, const void*, unsigned long, int, const void*, unsigned) { return 0; }

/* lUk6wrGXyMw#libScePosix -> recvfrom */
long recvfrom(int, void*, unsigned long, int, void*, unsigned*) { return 0; }

/* TXFFFiNldU8#libScePosix -> getpeername */
int getpeername(int, void*, unsigned*) { return 0; }

/* ioKMruft1ek#libSceDiscMap -> sceDiscMap_8A828CAEE7EDD5E9 */
int sceDiscMap_8A828CAEE7EDD5E9(void) { return 0; }

/* LwG8g3niqwA#libkernel -> sceKernelDlsym */
int sceKernelDlsym(int, char*, void*) { return 0; }

/* mKoTx03HRWA#libScePosix -> pthread_condattr_init */
int pthread_condattr_init(void* attr) { (void)attr; return 0; }

uintptr_t runtime_tlou_resolve(const char *name) {
    if (!strcmp(name, "k1SwgkMSOM8#libSceRemoteplay")) return (uintptr_t)&sceRemoteplayInitialize;
    if (!strcmp(name, "BOwybKVa3Do#libSceRemoteplay")) return (uintptr_t)&sceRemoteplayTerminate;
    if (!strcmp(name, "0Cq8ipKr9n0#libkernel")) return (uintptr_t)&sceKernelUtimes;
    if (!strcmp(name, "DHmwsa6S8Tc#libSceNpCommerce")) return (uintptr_t)&sceNpCommerceShowPsStoreIcon;
    if (!strcmp(name, "dsqCVsNM0Zg#libSceNpCommerce")) return (uintptr_t)&sceNpCommerceHidePsStoreIcon;
    if (!strcmp(name, "-Q1-u1a7p0g#libScePlayGo")) return (uintptr_t)&scePlayGoPrefetch;
    if (!strcmp(name, "3OMbYZBaa50#libScePlayGo")) return (uintptr_t)&scePlayGoGetLanguageMask;
    if (!strcmp(name, "Gl6w5i0JokY#libSceAppContent")) return (uintptr_t)&sceAppContentDownloadDataGetAvailableSpaceKb;
    if (!strcmp(name, "uvT2iYBBnkY#libkernel")) return (uintptr_t)&sceKernelSync;
    if (!strcmp(name, "Dbbkj6YHWdo#libSceCoredump")) return (uintptr_t)&sceCoredumpWriteUserData;
    if (!strcmp(name, "8zLSfEfW5AU#libSceCoredump")) return (uintptr_t)&sceCoredumpRegisterCoredumpHandler;
    if (!strcmp(name, "-LJbF9b-Who#libSceNpSns")) return (uintptr_t)&sceNpSnsFacebookAbortRequest;
    if (!strcmp(name, "iQr9UxPHUFs#libSceNpUtility")) return (uintptr_t)&sceNpLookupCreateRequest;
    if (!strcmp(name, "cdqOFyupRS4#libSceNpSnsFacebookDialog")) return (uintptr_t)&sceNpSnsFacebookDialogTerminate;
    if (!strcmp(name, "OoTjfxl8-wI#libSceNpSns")) return (uintptr_t)&sceNpSnsFacebookCreateRequest;
    if (!strcmp(name, "VtyS8XLBqNE#libSceNpSns")) return (uintptr_t)&sceNpSnsFacebookGetAccessToken;
    if (!strcmp(name, "pTvAKV1iQkE#libSceNpSns")) return (uintptr_t)&sceNpSnsFacebookDeleteRequest;
    if (!strcmp(name, "tdQArULbNQk#libSceNpSnsFacebookDialog")) return (uintptr_t)&sceNpSnsFacebookDialogInitialize;
    if (!strcmp(name, "Hi3onqHSN6M#libSceNpSnsFacebookDialog")) return (uintptr_t)&sceNpSnsFacebookDialogOpen;
    if (!strcmp(name, "fjV7C8H0Y8k#libSceNpSnsFacebookDialog")) return (uintptr_t)&sceNpSnsFacebookDialogUpdateStatus;
    if (!strcmp(name, "AifdcI1aKas#libSceNpSnsFacebookDialog")) return (uintptr_t)&sceNpSnsFacebookDialogGetResult;
    if (!strcmp(name, "zNGh-zoQTD0#libSceHttp")) return (uintptr_t)&sceHttpRemoveRequestHeader;
    if (!strcmp(name, "5LZA+KPISVA#libSceHttp")) return (uintptr_t)&sceHttpUriBuild;
    if (!strcmp(name, "IWalAn-guFs#libSceHttp")) return (uintptr_t)&sceHttpUriParse;
    if (!strcmp(name, "NxEI1KByvCI#libSceRtc")) return (uintptr_t)&sceRtcParseDateTime;
    if (!strcmp(name, "QBFoAIjJoXQ#libSceVoice")) return (uintptr_t)&sceVoiceSetVolume;
    if (!strcmp(name, "jjkCjneOYSs#libSceVoice")) return (uintptr_t)&sceVoiceGetVolume;
    if (!strcmp(name, "oUha0S-Ij9Q#libSceVoice")) return (uintptr_t)&sceVoiceSetMuteFlagAll;
    if (!strcmp(name, "gwUynkEgNFY#libSceVoice")) return (uintptr_t)&sceVoiceSetMuteFlag;
    if (!strcmp(name, "Pc4z1QjForU#libSceVoice")) return (uintptr_t)&sceVoiceGetMuteFlag;
    if (!strcmp(name, "2HajCEGgG4s#libSceNpSignaling")) return (uintptr_t)&sceNpSignalingGetPeerNetInfoResult;
    if (!strcmp(name, "AN3h0EBSX7A#libSceNpSignaling")) return (uintptr_t)&sceNpSignalingGetConnectionInfo;
    if (!strcmp(name, "b4qaXPzMJxo#libSceNpSignaling")) return (uintptr_t)&sceNpSignalingTerminateConnection;
    if (!strcmp(name, "GQ0hqmzj0F4#libSceNpSignaling")) return (uintptr_t)&sceNpSignalingGetConnectionFromNpId;
    if (!strcmp(name, "BdykpTwq2bs#libSceNpManager")) return (uintptr_t)&sceNpInGameMessageAbortHandle;
    if (!strcmp(name, "cE7wIsqXdZ8#libSceNpAuth")) return (uintptr_t)&sceNpAuthAbortRequest;
    if (!strcmp(name, "GFhVUpRmbHE#libSceNpManager")) return (uintptr_t)&sceNpInGameMessageInitialize;
    if (!strcmp(name, "s4UEa5iBJdc#libSceNpManager")) return (uintptr_t)&sceNpInGameMessageCreateHandle;
    if (!strcmp(name, "Vh1bhUG6mSs#libSceNpManager")) return (uintptr_t)&sceNpInGameMessagePrepare;
    if (!strcmp(name, "bMG3cVmUmuk#libSceNpManager")) return (uintptr_t)&sceNpInGameMessageTerminate;
    if (!strcmp(name, "6bwFkosYRQg#libSceNpAuth")) return (uintptr_t)&sceNpAuthCreateRequest;
    if (!strcmp(name, "ON7Sf5XEMmI#libSceNpManager")) return (uintptr_t)&sceNpInGameMessageSendData;
    if (!strcmp(name, "4n51s0zEf0c#libScePosix")) return (uintptr_t)&inet_pton;
    if (!strcmp(name, "4n51s0zEf0c#libkernel")) return (uintptr_t)&inet_pton;
    if (!strcmp(name, "7gxh+5QubhY#libSceAppContent")) return (uintptr_t)&sceAppContentAddcontEnqueueDownload;
    if (!strcmp(name, "VANhIWcqYak#libSceAppContent")) return (uintptr_t)&sceAppContentAddcontMount;
    if (!strcmp(name, "g3PNjYKWqnQ#libSceRemoteplay")) return (uintptr_t)&sceRemoteplayGetConnectionStatus;
    if (!strcmp(name, "PMVehSlfZ94#libSceIme")) return (uintptr_t)&sceImeKeyboardClose;
    if (!strcmp(name, "eaFXjfJv3xs#libSceIme")) return (uintptr_t)&sceImeKeyboardOpen;
    if (!strcmp(name, "dKadqZFgKKQ#libSceIme")) return (uintptr_t)&sceImeKeyboardGetResourceId;
    if (!strcmp(name, "-4GCfYdNF1s#libSceIme")) return (uintptr_t)&sceImeUpdate;
    if (!strcmp(name, "IuxnUuXk6Bg#libkernel")) return (uintptr_t)&sceKernelGetModuleList;
    if (!strcmp(name, "kUpgrXIrz7Q#libkernel")) return (uintptr_t)&sceKernelGetModuleInfo;
    if (!strcmp(name, "79M-JqvvGo0#libSceNpWebApi")) return (uintptr_t)&sceNpWebApiCreateHandle;
    if (!strcmp(name, "sIFx734+xys#libSceNpWebApi")) return (uintptr_t)&sceNpWebApiCreateServicePushEventFilter;
    if (!strcmp(name, "kJQJE0uKm5w#libSceNpWebApi")) return (uintptr_t)&sceNpWebApiRegisterServicePushEventCallback;
    if (!strcmp(name, "PfQ+f6ws764#libSceNpWebApi")) return (uintptr_t)&sceNpWebApiDeleteServicePushEventFilter;
    if (!strcmp(name, "B6HVJtDYxEE#libSceInvitationDialog")) return (uintptr_t)&sceInvitationDialogTerminate;
    if (!strcmp(name, "XvA5KS56wcs#libSceInvitationDialog")) return (uintptr_t)&sceInvitationDialogInitialize;
    if (!strcmp(name, "0zU0G+wiVLA#libSceInvitationDialog")) return (uintptr_t)&sceInvitationDialogOpen;
    if (!strcmp(name, "9+g9iOq+7kg#libSceInvitationDialog")) return (uintptr_t)&sceInvitationDialogUpdateStatus;
    if (!strcmp(name, "8XKR6wa64iQ#libSceInvitationDialog")) return (uintptr_t)&sceInvitationDialogGetResult;
    if (!strcmp(name, "DGMG3JshrZU#libkernel")) return (uintptr_t)&sceKernelSetVirtualRangeName;
    if (!strcmp(name, "asjUJJ+aa8s#libSceFiber")) return (uintptr_t)&sceFiberOptParamInitialize;
    if (!strcmp(name, "uq2Y5BFz0PE#libSceFiber")) return (uintptr_t)&sceFiberGetInfo;
    if (!strcmp(name, "JzyT91ucGDc#libSceFiber")) return (uintptr_t)&sceFiberRename;
    if (!strcmp(name, "fFxGkxF2bVo#libScePosix")) return (uintptr_t)&setsockopt;
    if (!strcmp(name, "fFxGkxF2bVo#libkernel")) return (uintptr_t)&setsockopt;
    if (!strcmp(name, "6O8EwYOgH9Y#libScePosix")) return (uintptr_t)&getsockopt;
    if (!strcmp(name, "6O8EwYOgH9Y#libkernel")) return (uintptr_t)&getsockopt;
    if (!strcmp(name, "oBr313PppNE#libScePosix")) return (uintptr_t)&sendto;
    if (!strcmp(name, "oBr313PppNE#libkernel")) return (uintptr_t)&sendto;
    if (!strcmp(name, "lUk6wrGXyMw#libScePosix")) return (uintptr_t)&recvfrom;
    if (!strcmp(name, "lUk6wrGXyMw#libkernel")) return (uintptr_t)&recvfrom;
    if (!strcmp(name, "TXFFFiNldU8#libScePosix")) return (uintptr_t)&getpeername;
    if (!strcmp(name, "TXFFFiNldU8#libkernel")) return (uintptr_t)&getpeername;
    if (!strcmp(name, "ioKMruft1ek#libSceDiscMap")) return (uintptr_t)&sceDiscMap_8A828CAEE7EDD5E9;
    if (!strcmp(name, "LwG8g3niqwA#libkernel")) return (uintptr_t)&sceKernelDlsym;
    if (!strcmp(name, "mKoTx03HRWA#libScePosix")) return (uintptr_t)&pthread_condattr_init;
    if (!strcmp(name, "mKoTx03HRWA#libkernel")) return (uintptr_t)&pthread_condattr_init;
    return 0;
}

/* Total stubs: 73 */

