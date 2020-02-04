"""
Lightest possible way of interfacing with the picoharp library. The
intention would be to then use this to make a further class that is user
friendly and actually does stuff.
"""

import time
import ctypes

import os
import platform
# TODO: Copy defines from phdefin.h and errorcodes.h here somewhere.


class LD_PharpDLL:
    """
    Determines the architecture and platform to know which library file to open
    (and where from) and then just makes available every function in the
    phlib.h without the user having to worry about ctypes everywhere.
    """

    def __init__(self, device_Number):
        """
        The examples seem to try and open all device numbers up to some limit
        (8?) and see what comes back. That seems weird so let's just have one
        instance of this class to interface with each device number and if a
        user really wants to do that way they can just try and instanciate
        multiple versions of this with different device numbers set.
        """

        os_Name = platform.system()
        arch = platform.architecture()[0]
        print(f"Detected {os_Name}, {arch}")

        if os_Name == "Linux":
            if arch == "64bit":
                dll_Path = os.path.abspath("/usr/local/lib64/ph300/phlib.so")
            else:
                dll_Path = os.path.abspath("/usr/local/lib/ph300/phlib.so")
        elif os_Name == "Windows":
            # TODO: Get the paths for Windows
            pass

        self.phlib = ctypes.CDLL(dll_Path)
        self.device_Number_ct = ctypes.c_int(device_Number)

    def Open(self):
        """
        extern int _stdcall PH_OpenDevice(int devidx, char* serial);
        """

        hwSerial_ct = ctypes.create_string_buffer(b"", 8)
        return_Code = self.phlib.PH_OpenDevice(self.device_Number_ct,
                                               hwSerial_ct)

        if return_Code == 0:
            device_Number = self.device_Number_ct.value
            hwSerial = hwSerial_ct.value.decode("utf-8")
            print(f"Connected to device {device_Number}, serial: {hwSerial}")
        else:
            self.ProcessReturnCode(return_Code)

        return return_Code

    def Close(self):
        """
        extern int _stdcall PH_CloseDevice(int devidx);
        """

        self.phlib.PH_CloseDevice(self.device_Number_ct)

    def Initialize(self, mode_Hist=0):
        """
        extern int _stdcall PH_Initialize(int devidx, int mode);
        """

        return_Code = self.phlib.PH_Initialize(self.device_Number_ct,
                                               ctypes.c_int(mode_Hist))

        # demo says at least 100ms should pass before reading count rates after
        # setting this solet's put a wait here for safety.
        time.sleep(0.2)

        return self.ProcessReturnCode(return_Code)

    def Calibrate(self):
        """
        extern int _stdcall PH_Calibrate(int devidx);
        """

        print("Calibrate")
        return_Code = self.phlib.PH_Calibrate(self.device_Number_ct)
        return self.ProcessReturnCode(return_Code)

    def Start(self, tacq=1000):
        """
        extern int _stdcall PH_StartMeas(int devidx, int tacq);
        """
        return_Code = self.phlib.PH_StartMeas(self.device_Number_ct,
                                              ctypes.c_int(tacq))
        print(f"Measuring for {tacq}ms")
        return self.ProcessReturnCode(return_Code)

    def Stop(self):
        """
        extern int _stdcall PH_StopMeas(int devidx);
        """

        return_Code = self.phlib.PH_StopMeas(self.device_Number_ct)
        print(f"Stopped")
        return self.ProcessReturnCode(return_Code)

#    def Read_FIFO(self):
#        """
#        extern int _stdcall PH_ReadFiFo(int devidx, unsigned int* buffer,
#        int count, int* nactual);
#        """
#        raise NotImplementedError

    def ClearHistMem(self):
        """
        extern int _stdcall PH_ClearHistMem(int devidx, int block);
        """
        return_Code = self.phlib.PH_ClearHistMem(self.device_Number_ct,
                                                 ctypes.c_int(0))
        return self.ProcessReturnCode(return_Code)

    def ProcessReturnCode(self, return_Code):
        """
        Print an error if there is one, otherwise return 0
        """
        # TODO: Replace with logging. Or something
        if return_Code == 0:
            return return_Code
        else:
            return self.Get_ErrorString(return_Code)

    def Get_BaseResolution(self):
        """
        extern int _stdcall PH_GetBaseResolution(int devidx,
        double* resolution, int* binsteps);
        """

        base_Res_ct = ctypes.c_double()
        return_Code = self.phlib.PH_GetBaseResolution(
                                                    self.device_Number_ct,
                                                    ctypes.byref(base_Res_ct))
        self.ProcessReturnCode(return_Code)

        return base_Res_ct.value

    def Get_CountRate(self):
        """
        extern int _stdcall PH_GetCountRate(int devidx, int channel,
        int* rate);
        """

        countRate0_ct = ctypes.c_int()
        countRate1_ct = ctypes.c_int()

        return_Code0 = self.phlib.PH_GetCountRate(self.device_Number_ct,
                                                  ctypes.c_int(0),
                                                  ctypes.byref(countRate0_ct))
        self.ProcessReturnCode(return_Code0)
        return_Code1 = self.phlib.PH_GetCountRate(self.device_Number_ct,
                                                  ctypes.c_int(1),
                                                  ctypes.byref(countRate1_ct))
        self.ProcessReturnCode(return_Code1)

        return countRate0_ct.value, countRate1_ct.value

    def Get_CTCStatus(self):
        """
        extern int _stdcall PH_CTCStatus(int devidx, int* ctcstatus);
        """
        ctc_Status_ct = ctypes.c_int(0)
        return_Code = self.phlib.PH_CTCStatus(self.device_Number_ct,
                                              ctypes.byref(ctc_Status_ct))
        self.ProcessReturnCode(return_Code)
        return ctc_Status_ct.value

    def Get_ElapsedMeasTime(self):
        """
        extern int _stdcall PH_GetElapsedMeasTime(int devidx, double* elapsed);
        """
        meas_Time_ct = ctypes.c_double()
        return_Code = self.phlib.PH_GetElapsedMeasTime(self.device_Number_ct,
                                                       ctypes.byref(meas_Time_ct))
        self.ProcessReturnCode(return_Code)

        return meas_Time_ct.value

    def Get_ErrorString(self, return_Code):
        """
        extern int _stdcall PH_GetErrorString(char* errstring, int errcode);
        """

        errorString_ct = ctypes.create_string_buffer(b"", 40)
        self.phlib.PH_GetErrorString(errorString_ct, ctypes.c_int(return_Code))
        error_String = errorString_ct.value.decode("utf-8")

        print(f"Return code {return_Code} is {error_String}")
        return error_String

    def Get_Features(self):
        """
        extern int _stdcall PH_GetFeatures(int devidx, int* features);
        """
        raise NotImplementedError

    def Get_Flags(self):
        """
        extern int _stdcall PH_GetFlags(int devidx, int* flags);
        """

        flags_ct = ctypes.c_int()
        return_Code = self.phlib.PH_GetFlags(self.device_Number_ct,
                                             ctypes.byref(flags_ct))
        self.ProcessReturnCode(return_Code)
        return flags_ct.value

    def Get_HarwareDebugInfo(self):
        """
        extern int _stdcall PH_GetHardwareDebugInfo(int devidx,
        char *debuginfo);
        """
        raise NotImplementedError

    def Get_HardwareInfo(self):
        """
        extern int _stdcall PH_GetHardwareInfo(int devidx, char* model,
        char* partno, char* version);
        """

        hwPartno_ct = ctypes.create_string_buffer(b"", 8)
        hwVersion_ct = ctypes.create_string_buffer(b"", 8)
        hwModel_ct = ctypes.create_string_buffer(b"", 16)

        return_Code = self.phlib.PH_GetHardwareInfo(self.device_Number_ct,
                                                    hwModel_ct,
                                                    hwPartno_ct,
                                                    hwVersion_ct)
        if return_Code == 0:
            hw_Model = hwModel_ct.value.decode("utf-8")
            hw_Part = hwPartno_ct.value.decode("utf-8")
            hw_Vers = hwVersion_ct.value.decode("utf-8")

            print(f"Found model: {hw_Model}, part: {hw_Part}, ver: {hw_Vers}")
        self.ProcessReturnCode(return_Code)

        return {"model": hw_Model,
                "part": hw_Part,
                "version": hw_Vers}

    def Get_Histogram(self, histogram_Channels):
        """
        extern int _stdcall PH_GetHistogram(int devidx, unsigned int* chcount,
        int block);
        """
        #print(f"Get histogram")
        counts_ct = (ctypes.c_uint * histogram_Channels)()
        return_Code = self.phlib.PH_GetHistogram(self.device_Number_ct,
                                                 ctypes.byref(counts_ct),
                                                 ctypes.c_int(0))
        self.ProcessReturnCode(return_Code)

        #print(f"Process histogram")
        histogram = [x for x in counts_ct]
        return histogram

    def Get_LibraryVersion(self):
        """
        extern int _stdcall PH_GetLibraryVersion(char* version);
        """

        libVersion_ct = ctypes.create_string_buffer(b"", 8)
        self.phlib.PH_GetLibraryVersion(libVersion_ct)
        lib_Version = libVersion_ct.value.decode("utf-8")

        print(f"Library version is {lib_Version}")
        return lib_Version

    def Get_Resolution(self):
        """
        extern int _stdcall PH_GetResolution(int devidx, double* resolution);
        """

        resolution = ctypes.c_double()
        return_Code = self.phlib.PH_GetResolution(self.device_Number_ct,
                                                  ctypes.byref(resolution))
        self.ProcessReturnCode(return_Code)
        return resolution.value

#    def Get_RouterVersion(self):
#        """
#        extern int _stdcall PH_GetRouterVersion(int devidx, char* model,
#        char* version);
#        """
#        raise NotImplementedError

#    def Get_RoutingChannels(self):
#        """
#        extern int _stdcall PH_GetRoutingChannels(int devidx, int* rtchannels);
#        """
#        raise NotImplementedError

    def Get_SerialNumber(self):
        """
        extern int _stdcall PH_GetSerialNumber(int devidx, char* serial);
        """
        raise NotImplementedError

    def Get_Warnings(self):
        """
        extern int _stdcall PH_GetWarnings(int devidx, int* warnings);
        """
        raise NotImplementedError

    def Get_WarningsText(self):
        """
        extern int _stdcall PH_GetWarningsText(int devidx, char* text,
        int warnings);
        """
        raise NotImplementedError

    def Set_Binning(self, binning):
        """
        extern int _stdcall PH_SetBinning(int devidx, int binning);
        """

        print("Set binning")
        return_Code = self.phlib.PH_SetBinning(self.device_Number_ct,
                                               ctypes.c_int(binning))
        return self.ProcessReturnCode(return_Code)

    def Set_InputCFD(self, cfd0_level, cfd0_zerocross,
                     cfd1_level, cfd1_zerocross):
        """
        extern int _stdcall PH_SetInputCFD(int devidx, int channel, int level,
        int zc);
        """
        print("Set Input CFD channel 0")
        return_Code0 = self.phlib.PH_SetInputCFD(self.device_Number_ct,
                                                 ctypes.c_int(0),
                                                 ctypes.c_int(cfd0_level),
                                                 ctypes.c_int(cfd0_zerocross))
        print("Set Input CFD channel 1")
        return_Code1 = self.phlib.PH_SetInputCFD(self.device_Number_ct,
                                                 ctypes.c_int(1),
                                                 ctypes.c_int(cfd1_level),
                                                 ctypes.c_int(cfd1_zerocross))
        return self.ProcessReturnCode(return_Code0), \
            self.ProcessReturnCode(return_Code1)

#    def Set_MarkerEdges(self):
#        """
#        extern int _stdcall PH_SetMarkerEdges(int devidx, int me0, int me1,
#        int me2, int me3);
#        """
#        raise NotImplementedError

#    def Set_MarkerEnable(self):
#        """
#        extern int _stdcall PH_SetMarkerEnable(int devidx, int en0, int en1,
#        int en2, int en3);
#        """
#        raise NotImplementedError

#    def Set_MarkerHoldoffTime(self):
#        """
#        extern int _stdcall PH_SetMarkerHoldoffTime(int devidx,
#        int holdofftime);
#        """
#        raise NotImplementedError

    def Set_MultistopEnable(self):
        """
        extern int _stdcall PH_SetMultistopEnable(int devidx, int enable);
        """
        raise NotImplementedError

    def Set_Offset(self):
        """
        extern int _stdcall PH_SetOffset(int devidx, int offset);
        """
        raise NotImplementedError

#    def Set_PHR800CFD(self):
#        """
#        extern int _stdcall PH_SetPHR800CFD(int devidx, int channel,
#        int level, int zc);
#        """
#        raise NotImplementedError

#    def Set_PHR800Input(self):
#        """
#        extern int _stdcall PH_SetPHR800Input(int devidx, int channel,
#        int level, int edge);
#        """
#        raise NotImplementedError

#    def Set_RoutingChannelOffset(self):
#        """
#        extern int _stdcall PH_SetRoutingChannelOffset(int devidx, int channel,
#        int offset);
#        """
#        raise NotImplementedError

#    def Set_RoutingEnable(self):
#        """
#        extern int _stdcall PH_EnableRouting(int devidx, int enable);
#        """
#        raise NotImplementedError

    def Set_StopOverflow(self):
        """
        extern int _stdcall PH_SetStopOverflow(int devidx, int stop_ovfl,
        int stopcount);
        """

        return_Code = self.phlib.PH_SetStopOverflow(self.device_Number_ct,
                                                    ctypes.c_int(1),
                                                    ctypes.c_int(65535))
        return self.ProcessReturnCode(return_Code)

    def Set_SyncDiv(self, sync_Divider):
        """
        extern int _stdcall PH_SetSyncDiv(int devidx, int div);
        """

        print("Set Sync Divider")
        return_Code = self.phlib.PH_SetSyncDiv(self.device_Number_ct,
                                               ctypes.c_int(sync_Divider))

        # demo says at least 100ms should pass before reading count rates after
        # setting this solet's put a wait here for safety.
        time.sleep(0.2)

        return self.ProcessReturnCode(return_Code)

    def Set_SyncOffset(self, sync_Offset):
        """
        extern int _stdcall PH_SetSyncOffset(int devidx, int syncoffset);
        """

        print("Set Ch0 Offset")
        return_Code = self.phlib.PH_SetOffset(self.device_Number_ct,
                                              ctypes.c_int(sync_Offset))
        return self.ProcessReturnCode(return_Code)
