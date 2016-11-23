import logging
import inspect
import subprocess
import zmq
import time

from uniflex.core import exceptions
from .ath_module import AthModule

__author__ = "Piotr Gawlowicz, Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz, zubow}@tkn.tu-berlin.de"

"""
    Atheros ATH9k specific functionality.
"""
class Ath9kModule(AthModule):
    def __init__(self, local_mac_processor_port=1217):
        super(Ath9kModule, self).__init__()
        self.log = logging.getLogger('Ath9kModule')
        # Used by local controller for communication with mac processor
        self.local_mac_processor_port = local_mac_processor_port
        # set-up executable here. note: it is platform-dependent
        self.exec_file = 'hmac_userspace_daemon'

    ''' HMAC '''

    def install_mac_processor(self, interface, hybridMac):
        """
        Installs hMAC configuration and activates hMAC
        :param interface: the name of the interface
        :param hybridMac: the hMAC configuration
        :return:
        """
        self.log.info('Function: installMacProcessor on iface: %s' % interface)

        try:
            # create configuration string
            conf_str = hybridMac.createConfString()

            processArgs = str(self.exec_file) + " -d 0 " + " -i" +str(interface) + " -f" + str(hybridMac.getSlotDuration()) + " -n" + str(hybridMac.getNumSlots()) + " -c" + conf_str
            self.log.info('Install hMAC executable w/ = %s' % str(processArgs))

            # run as background process
            subprocess.Popen(processArgs.split(), shell=False)

            self.hmac_ctrl_socket = None
            return True
        except Exception as e:
            self.log.fatal("Failed to install MAC processor on %s: err_msg: %s" % (interface, e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to install MAC processor; check HMAC installation.: ' + str(e))

    def update_mac_processor(self, interface, hybridMac):
        ''' Updates hMAC configuration of a running hMAC '''
        self.log.info('Function: updateMacProcessor on iface: %s' % interface)

        try:
            # create configuration string
            conf_str = hybridMac.createConfString()

            if self.hmac_ctrl_socket is None:
                context = zmq.Context()
                self.hmac_ctrl_socket = context.socket(zmq.REQ)
                self.hmac_ctrl_socket.connect("tcp://localhost:" + str(self.local_mac_processor_port))

            #  update MAC processor configuration
            self.log.info("Send ctrl req message to HMAC: %s" % conf_str)
            self.hmac_ctrl_socket.send(conf_str)
            message = self.hmac_ctrl_socket.recv()
            self.log.info("Received ctrl reply message from HMAC: %s" % message)
            return True
        except zmq.ZMQError as e:
            self.log.fatal("Update MAC processor failed: %s" % (e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Update MAC processor failed: ' + str(e))

    def uninstall_mac_processor(self, interface, hybridMac):

        self.log.info('Function: uninstallMacProcessor on iface: %s' % interface)

        try:
            # set allow all configuration string
            conf_str = hybridMac.createAllowAllConfString()

            # command string
            terminate_str = 'TERMINATE'

            if self.hmac_ctrl_socket is None:
                context = zmq.Context()
                self.hmac_ctrl_socket = context.socket(zmq.REQ)
                self.hmac_ctrl_socket.connect("tcp://localhost:" + str(self.local_mac_processor_port))

            #  update MAC processor configuration
            self.log.info("Send ctrl req message to HMAC: %s" % conf_str)
            self.hmac_ctrl_socket.send(conf_str)
            message = self.hmac_ctrl_socket.recv()
            self.log.info("Received ctrl reply from HMAC: %s" % message)

            # give one second to settle down
            time.sleep(1)

            # send termination signal to MAC
            self.hmac_ctrl_socket.send(terminate_str)
            message = self.hmac_ctrl_socket.recv()
            self.log.info("Received ctrl reply from HMAC: %s" % message)

            return True
        except zmq.ZMQError as e:
            self.log.fatal("Failed to uninstall MAC processor %s" % str(e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to uninstall MAC processor: ' + str(e))

    ''' Radio sensitivity '''

    def configure_radio_sensitivity(self, phy_dev, **kwargs):

        '''
            Configuring the carrier receiving sensitivity of the radio.
            Req.: modprobe ath5k/9k debug=0xffffffff

            #configuration of ath5k's ANI settings
            # disable ani
            echo "0" > /sys/kernel/debug/ieee80211/phy0/ath9k/ani

            supported ani modes:
            - 0 - disable ANI
            - tbd
        '''
        prefix = 'ath9k'
        ani_mode = kwargs.get('ani_mode')
        self.log.info('Setting ANI sensitivity w/ = %s' % str(ani_mode))

        try:
            myfile = open('/sys/kernel/debug/ieee80211/' + phy_dev + '/' + prefix + '/ani', 'w')
            myfile.write(ani_mode)
            myfile.close()
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=fname, err_msg=str(e))

        return True
