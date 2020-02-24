"""
Uses LD_PharpDLL to make an interface to the Picoharp300's histogramming
mode for humans to use.
"""

import logging
import numpy as np
import scipy.signal
import time

class LD_Pharp:
    def __init__(self, device_Number=0):
        self.logger = logging.getLogger("PHarp")
        logging.basicConfig(level=logging.DEBUG)

        """
        Binning:
            How many bins of width "resolution" to combine to output the
            histogram. Number of bins combined are 2**binning. Changes the
            resolution by this factor compared to the base resolution.
        Sync Offset:
            Emulates adding a cable delay to sync input (ch0)
            (+ve value is longer delay)
        Acquisition Time:
            In milliseconds.
        Sync_Divider:
            Divides the clock on the sync channel (ch0)
        CFD_...:
            Zerocross and discriminator level for channels 0 and 1

        """

        self._default_Options = {
                "binning": 0,
                "sync_Offset": 0,
                "sync_Divider": 1,
                "CFD0_ZeroCross": 10,
                "CFD0_Level": 50,
                "CFD1_ZeroCross": 10,
                "CFD1_Level": 50,
                "acq_Time": 500
                }
        self.options = self._default_Options

        self.base_Resolution = 4.0  # picoseconds
        self.resolution = self.base_Resolution

        self.options = self._default_Options

    def __del__(self):
        self.logger.debug(f"Bye")

    def Update_Settings(self, sync_Divider, sync_Offset, CFD0_Level,
                        CFD0_ZeroCross, CFD1_Level, CFD1_ZeroCross, binning,
                        acq_Time):
        """
        Even though args are best sent as an unpacked dict, enforcing the
        parameters separately enforces that they all get sent.
        """

        # Rebuild the options dict so it can be remembered.
        new_Options = {
                "binning": binning,
                "sync_Offset": sync_Offset,
                "sync_Divider": sync_Divider,
                "CFD0_ZeroCross": CFD0_ZeroCross,
                "CFD0_Level": CFD0_Level,
                "CFD1_ZeroCross": CFD1_ZeroCross,
                "CFD1_Level": CFD1_Level,
                "acq_Time": acq_Time
                }
        # Put the new dictionary where the old one was
        self.options = new_Options

        new_Resolution = self.base_Resolution * (2 ** self.options["binning"])
        self.logger.debug(f"Asked for resolution {new_Resolution}")
        # Check that the resolution requested is the same as the resolution
        # the Picoharp thinks it's providing.
        self.resolution = new_Resolution
        self.logger.debug(f"New resolution is {self.resolution}")

    def Get_CountRate(self):
        """
        Returns both channel count rates in a python list.
        """

        return np.random.randint(0,65535, 2)

    def Get_A_Histogram(self, n_Channels=65536):
        """
        Returns the time tagging histogram as a python list. It's always the
        full number of channels that can be supplied by the Picoharp. They can
        be trimmed later.
        """

        gaussian = scipy.signal.gaussian(25000, 1000) * 25000

        moved = np.roll(gaussian, np.random.randint(-255,255))

        noise = np.random.normal(0, 1000, 25000)
        noise -= noise.min()

        final = gaussian + noise

        time.sleep(self.options["acq_Time"] / 1000)

        return final


if __name__ == "__main__":
    my_LDPharp = LD_Pharp()

    print(f"Count rate: {my_LDPharp.Get_CountRate()}")

    import matplotlib.pyplot as plt
    plt.plot(my_LDPharp.Get_A_Histogram())
