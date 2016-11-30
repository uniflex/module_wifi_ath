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
    Atheros ATH9k specific functionality:
    - hybrid TDMA/CSMA
    - sensitivity control
"""
class Ath9kModule(AthModule):
    def __init__(self, local_mac_processor_port=1217):
        super(Ath9kModule, self).__init__()
        self.log = logging.getLogger('Ath9kModule')
        # Used by local controller for communication with mac processor
        self.local_mac_processor_port = local_mac_processor_port
        # set-up executable here. note: it is platform-dependent
        self.exec_file = 'hmac_userspace_daemon'
        self.prefix = 'ath9k'
        self.active_hmac_conf = None

    ''' HMAC '''

    def activate_radio_program(self, hmac_name, hmac_conf, interface=None):
        """
        Installs hMAC configuration and activates hMAC
        :param hmac_name: name of the HMAC conf; used as ID internally
        :param hmac_conf: the hMAC configuration
        :param iface: the name of interface
        :return: True if successful
        """

        self.log.info('Function: activate_radio_program')

        try:
            if interface == None:
                self.log.warn('Iface is required')
                return

            # create configuration string
            conf_str = hmac_conf.createConfString()

            processArgs = str(self.exec_file) + " -d 0 " + " -i" +str(interface) \
                          + " -f" + str(hmac_conf.getSlotDuration()) + " -n" + str(hmac_conf.getNumSlots()) \
                          + " -c" + conf_str

            self.log.info('Install hMAC executable w/ = %s' % str(processArgs))

            # run as background process
            subprocess.Popen(processArgs.split(), shell=False)

            self.active_hmac_conf = hmac_conf
            self.hmac_ctrl_socket = None
            return True
        except Exception as e:
            self.log.fatal("Failed to install MAC processor on %s: err_msg: %s" % (interface, e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to install MAC processor; check HMAC installation.: ' + str(e))


    def update_radio_program(self, hmac_name, hmac_conf, interface=None):
        """
        Updates a running hMAC configuration on-the-fly
        :param hmac_name: hmac name/ID
        :param hmac_conf: the hMac configuration
        :param interface: the name of interface
        :return: True if successful
        """

        self.log.info('Function: update_radio_program')

        try:
            if interface == None:
                self.log.warn('Iface is required')
                return

            # create configuration string
            conf_str = hmac_conf.createConfString()

            if self.hmac_ctrl_socket is None:
                context = zmq.Context()
                self.hmac_ctrl_socket = context.socket(zmq.REQ)
                self.hmac_ctrl_socket.connect("tcp://localhost:" + str(self.local_mac_processor_port))

            #  update MAC processor configuration
            self.log.info("Send ctrl req message to HMAC: %s" % conf_str)
            self.hmac_ctrl_socket.send(conf_str.encode('ascii'))
            message = self.hmac_ctrl_socket.recv()
            self.log.info("Received ctrl reply message from HMAC: %s" % message)
            self.active_hmac_conf = hmac_conf

            return True
        except zmq.ZMQError as e:
            self.log.fatal("Update MAC processor failed: %s" % (e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Update MAC processor failed: ' + str(e))


    def deactivate_radio_program(self, hmac_name, do_pause=False):
        """
        Stops running hMAC configuration, i.e. standard CSMA/CA is used afterwards.
        :param hmac_name: the name of the HMAC to be deactivated; the last loaded in case of None
        :param do_pause: just pause or terminate
        :return: True if successful
        """
        self.log.info('Function: deactivate_radio_program')

        try:
            if self.active_hmac_conf == None:
                self.log.warn('No hMAC was activated before; ignoring.')
                return

            # set allow all configuration string
            conf_str = self.active_hmac_conf.createAllowAllConfString()

            # command string
            terminate_str = 'TERMINATE'

            if self.hmac_ctrl_socket is None:
                context = zmq.Context()
                self.hmac_ctrl_socket = context.socket(zmq.REQ)
                self.hmac_ctrl_socket.connect("tcp://localhost:" + str(self.local_mac_processor_port))

            #  update MAC processor configuration
            self.log.info("Send ctrl req message to HMAC: %s" % conf_str)
            self.hmac_ctrl_socket.send(conf_str.encode('ascii'))
            message = self.hmac_ctrl_socket.recv()
            self.log.info("Received ctrl reply from HMAC: %s" % message)

            # give one second to settle down
            time.sleep(1)

            # send termination signal to MAC
            self.hmac_ctrl_socket.send(terminate_str)
            message = self.hmac_ctrl_socket.recv()
            self.log.info("Received ctrl reply from HMAC: %s" % message)

            self.active_hmac_conf = None
            return True
        except zmq.ZMQError as e:
            self.log.fatal("Failed to uninstall MAC processor %s" % str(e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to uninstall MAC processor: ' + str(e))

    ''' Radio sensitivity '''

    def configure_radio_sensitivity(self, ani_mode):
        """
        Configuring the carrier receiving sensitivity of the radio.
        Req.: modprobe ath5k/9k debug=0xffffffff
        Supported ani modes:
        - 0 - disable ANI
        - tbd
        :param ani_mode: The ANI mode, 0=disable, other=tbd
        :return: True if successful
        """

        self.log.info('Setting ANI sensitivity w/ = %s' % str(ani_mode))

        try:
            myfile = open('/sys/kernel/debug/ieee80211/' + self.phyName + '/' + self.prefix + '/ani', 'w')
            myfile.write(ani_mode)
            myfile.close()
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=fname, err_msg=str(e))

        return True
