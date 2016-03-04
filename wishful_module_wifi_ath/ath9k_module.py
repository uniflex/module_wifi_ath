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
from ath_module import AthModule

__author__ = "Piotr Gawlowicz, Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz, zubow}@tkn.tu-berlin.de"


@wishful_module.build_module
class Ath9kModule(AthModule):
    def __init__(self):
        super(Ath9kModule, self).__init__()
        self.log = logging.getLogger('Ath9kModule')

    @wishful_module.bind_function(upis.radio.configure_radio_sensitivity)
    def configure_radio_sensitivity(self, phy_dev, **kwargs):
        self.log.warn('Untested !!! Please test me !!!')
        raise exceptions.UnsupportedUPIFunctionException(func_name='radio.configure_radio_sensitivity', conn_module='wifi_ath9k')
        #return super(Ath9kModule, self).configure_radio_sensitivity(phy_dev, 'ath9k', **kwargs)

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
