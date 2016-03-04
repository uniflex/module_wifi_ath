import logging
import random
import wishful_upis as upis
import wishful_agent as wishful_module
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
class Ath9kModule(wishful_module_wifi.WifiModule):
    def __init__(self):
        super(Ath9kModule, self).__init__()
        self.log = logging.getLogger('ath9k_module.main')
        self.interface = "wlan0"
        self.channel = 1
        self.power = 1

    @wishful_module.bind_function(upis.radio.set_power)
    def set_power(self, power):
        self.log.debug("ATH9K sets power: {} on interface: {}".format(power, self.interface))
        self.power = power
        return {"SET_POWER_OK_value" : power}


    @wishful_module.bind_function(upis.radio.get_power)
    def get_power(self):
        self.log.debug("ATH9K gets power on interface: {}".format(self.interface))
        return self.power


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


    @wishful_module.bind_function(upis.radio.inject_frame)
    def inject_frame(self, frame):
        self.log.debug("Inject frame".format())
        return 0


    @wishful_module.bind_function(upis.radio.install_mac_processor)
    def install_mac_processor(self, interface, mac_profile):

        self.log.info('Function: installMacProcessor')
        self.log.info('margs = %s' % str(myargs))

        hybridMac = pickle.loads(mac_profile)

        conf_str = None
        for ii in range(hybridMac.getNumSlots()): # for each slot
            ac = hybridMac.getAccessPolicy(ii)
            entries = ac.getEntries()

            for ll in range(len(entries)):
                entry = entries[ll]

                # slot_id, mac_addr, tid_mask
                if conf_str is None:
                    conf_str = str(ii) + "," + str(entry[0]) + "," + str(entry[1])
                else:
                    conf_str = conf_str + "#" + str(ii) + "," + str(entry[0]) + "," + str(entry[1])

        # set-up executable here. note: it is platform-dependent

        exec_file = str(os.path.join(self.getPlatformPathHybridMAC())) + '/hybrid_tdma_csma_mac'

        processArgs = str(exec_file) + " -d 0 " + " -i" +str(interface) + " -f" + str(hybridMac.getSlotDuration()) + " -n" + str(hybridMac.getNumSlots()) + " -c" + conf_str
        self.log.info('Calling hybrid mac executable w/ = %s' % str(processArgs))

        try:
            # run as background process
            subprocess.Popen(processArgs.split(), shell=False)
            return True
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.UPIFunctionExecutionFailedException(func_name=fname, err_msg=str(e))

    @wishful_module.bind_function(upis.radio.update_mac_processor)
    def update_mac_processor(self, interface, mac_profile):

        self.log.info('Function: updateMacProcessor')
        self.log.info('margs = %s' % str(myargs))

        hybridMac = pickle.loads(mac_profile)

        # generate configuration string
        conf_str = None
        for ii in range(hybridMac.getNumSlots()): # for each slot
            ac = hybridMac.getAccessPolicy(ii)
            entries = ac.getEntries()

            for ll in range(len(entries)):
                entry = entries[ll]

                # slot_id, mac_addr, tid_mask
                if conf_str is None:
                    conf_str = str(ii) + "," + str(entry[0]) + "," + str(entry[1])
                else:
                    conf_str = conf_str + "#" + str(ii) + "," + str(entry[0]) + "," + str(entry[1])

        #  update MAC processor configuration
        try:
            # todo cache sockets!!!
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://localhost:" + str(LOCAL_MAC_PROCESSOR_CTRL_PORT))
            #socket.connect("ipc:///tmp/localmacprocessor")

            socket.send(conf_str)
            message = socket.recv()
            self.log.info("Received reply from HMAC: %s" % message)
            return True
        except zmq.ZMQError as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.UPIFunctionExecutionFailedException(func_name=fname, err_msg=str(e))

    @wishful_module.bind_function(upis.radio.uninstall_mac_processor)
    def uninstall_mac_processor(self, interface, mac_profile):
        import pickle

        self.log.info('Function: uninstallMacProcessor')

        hybridMac = pickle.loads(mac_profile)

        # set allow all
        # generate configuration string
        conf_str = None
        for ii in range(hybridMac.getNumSlots()): # for each slot
            # slot_id, mac_addr, tid_mask
            if conf_str is None:
                conf_str = str(ii) + "," + 'FF:FF:FF:FF:FF:FF' + "," + str(255)
            else:
                conf_str = conf_str + "#" + str(ii) + "," + 'FF:FF:FF:FF:FF:FF' + "," + str(255)

        # command string
        terminate_str = 'TERMINATE'

        #  update MAC processor configuration
        try:
            # todo cache sockets!!!
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://localhost:" + str(LOCAL_MAC_PROCESSOR_CTRL_PORT))
            #socket.connect("ipc:///tmp/localmacprocessor")

            # (1) set new config
            socket.send(conf_str)
            message = socket.recv()
            self.log.info("Received reply from HMAC: %s" % message)

            # give one second to settle down
            time.sleep(1)

            # (2) terminate MAC
            socket.send(terminate_str)
            message = socket.recv()
            self.log.info("Received reply from HMAC: %s" % message)

            return True
        except zmq.ZMQError as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.UPIFunctionExecutionFailedException(func_name=fname, err_msg=str(e))

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

    #################################################
    # Helper functions
    #################################################

    def get_platform_path_hybrid_MAC(self):
        '''
        Path to platform dependent (native) binaries: here hybrid MAC
        '''
        PLATFORM_PATH = os.path.join(".", "runtime", "connectors", "dot80211_linux", "hybridmac", "bin")
        pl = platform.architecture()
        sys = platform.system()
        machine = platform.machine()
        return os.path.join(PLATFORM_PATH, sys, pl[0], machine)

    def getPlatformPathSpectralScan(self):
        """
        Path to platform dependent (native) binaries: here spectral scanning
        """
        PLATFORM_PATH = os.path.join(".", "runtime", "connectors", "dot80211_linux", "ath_spec_scan", "bin")
        pl = platform.architecture()
        sys = platform.system()
        machine = platform.machine()
        return os.path.join(PLATFORM_PATH, sys, pl[0], machine)
