import logging
import random
import wishful_upis as upis
import wishful_framework as wishful_module
import wishful_module_wifi
import pickle
import os
from wishful_framework.classes import exceptions
import inspect
import subprocess
import zmq
import time
import platform
import numpy as np
import wishful_framework.upi_arg_classes.edca as edca #<----!!!!! Important to include it here; otherwise cannot be pickled!!!!


__author__ = "Piotr Gawlowicz, Mikolaj Chwalisz, Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz, chwalisz, zubow}@tkn.tu-berlin.de"

# Used by local controller for communication with mac processor
LOCAL_MAC_PROCESSOR_CTRL_PORT = 1217

@wishful_module.build_module
class AthModule(wishful_module_wifi.WifiModule):
    def __init__(self):
        super(AthModule, self).__init__()
        self.log = logging.getLogger('AthModule')
        self.interface = "wlan0"
        self.channel = 1
        self.power = 1

    @wishful_module.bind_function(upis.radio.set_mac_access_parameters)
    def setEdcaParameters(self, queueId, queueParams):
        self.log.debug("ATH9K sets EDCA parameters for queue: {} on interface: {}".format(queueId, self.interface))

        print "Setting EDCA parameters for queue: {}".format(queueId)
        print "AIFS: {}".format(queueParams.getAifs())
        print "CwMin: {}".format(queueParams.getCwMin())
        print "CwMax: {}".format(queueParams.getCwMax())
        print "TxOp: {}".format(queueParams.getTxOp())

        return 0


    @wishful_module.bind_function(upis.radio.get_noise)
    def get_noise(self):
        self.log.debug("Get Noise".format())
        return random.randint(-120, -30)


    @wishful_module.bind_function(upis.radio.get_airtime_utilization)
    def get_airtime_utilization(self):
        self.log.debug("Get Airtime Utilization".format())
        return random.random()


    @wishful_module.bind_function(upis.radio.perform_spectral_scanning)
    def perform_spectral_scanning(self, iface, freq_list, mode):
        """
            Perform active spectral scanning
        """

        self.log.debug('performActiveSpectralScanning on iface %s for freq=%s' % (iface, freq_list))

        exec_file = str(os.path.join(self.getPlatformPathSpectralScan())) + '/scan.sh'
        command = exec_file + " " + iface + " /tmp/out \"" + freq_list + "\""

        self.log.debug('command: %s' % command)

        try:
            # perform scanning
            [rcode, sout, serr] = self.run_command(command)

            if serr:
                self.log.warn("standard error of subprocess:")
                self.log.warn(serr)
                raise Exception("Error occured during spectrum scanning: %s" % serr)

            # perform parsing results
            self.log.debug('parsing scan results ...')

            tmpfile = '/tmp/out.dat'
            res = []
            with open(tmpfile) as f:
                content = f.readlines()

                for line in content:
                    arr = line.split(',')
                    res.append(arr)

            # cleanup
            os.remove(tmpfile)

            self.log.info('spec scan size %d' % len(res))

            if mode == 0:
                # return just raw samples
                return res
            elif mode == 1:
                # return the max/mean signal for each frequency bin only
                y = np.array(res)
                y = y.astype(np.float)
                uniq_freq = np.unique(y[:,0])
                uniq_freq.sort(axis=0)
                ret = []
                for v in np.nditer(uniq_freq.T):
                    v2 = np.asscalar(v)

                    a = y[np.logical_or.reduce([y[:,0] == x for x in (v2,)])]
                    sig = a[:,7].astype(np.float)
                    max_sig = 100
                    sig = sig[sig < max_sig]

                    max_v = np.ndarray.max(sig)
                    mean_v = np.ndarray.mean(sig)

                    #print('max: ', max_v)
                    #print('mean: ', mean_v)
                    ret.append([np.asscalar(v), max_v, mean_v])

                return ret
            else:
                raise Exception("Unknown mode type %s" % str(mode))

        except Exception as e:
            self.log.fatal("An error occurred in Dot80211Linux: %s" % e)
            raise Exception("An error occurred in Dot80211Linux: %s" % e)


    def configure_radio_sensitivity(self, phy_dev, prefix, **kwargs):
        '''
            Configuring the carrier receiving sensitivity of the radio.
            Req.: modprobe ath5k/9k debug=0xffffffff

            #configuration of ath5k's ANI settings
            echo "ani-off" > /sys/kernel/debug/ieee80211/phy0/ath5k/ani

            supported ani modes:
            - sens-low
            - sens-high
            - ani-off
            - ani-on
            - noise-low
            - noise-high
            - spur-low
            - spur-high
            - fir-low
            - fir-high
            - ofdm-off
            - ofdm-on
            - cck-off
            - cck-on

            Documentation from Linux Kernel:

            Adaptive Noise Immunity (ANI) controls five noise immunity parameters
            depending on the amount of interference in the environment, increasing
            or reducing sensitivity as necessary.

            The parameters are:

            - "noise immunity"
            - "spur immunity"
            - "firstep level"
            - "OFDM weak signal detection"
            - "CCK weak signal detection"

            Basically we look at the amount of ODFM and CCK timing errors we get and then
            raise or lower immunity accordingly by setting one or more of these
            parameters.
        '''

        ani_mode = kwargs.get('ani_mode')
        self.log.info('Setting ANI sensitivity w/ = %s' % str(ani_mode))

        try:
            myfile = open('/sys/kernel/debug/ieee80211/' + phy_dev + '/' + prefix + '/ani', 'w')
            myfile.write(ani_mode)
            myfile.close()
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.UPIFunctionExecutionFailedException(func_name=fname, err_msg=str(e))
        
        return True

    #################################################
    # Helper functions
    #################################################

    def getPlatformPathSpectralScan(self):
        """
        Path to platform dependent (native) binaries: here spectral scanning
        """
        PLATFORM_PATH = os.path.join(".", "runtime", "connectors", "dot80211_linux", "ath_spec_scan", "bin")
        pl = platform.architecture()
        sys = platform.system()
        machine = platform.machine()
        return os.path.join(PLATFORM_PATH, sys, pl[0], machine)
