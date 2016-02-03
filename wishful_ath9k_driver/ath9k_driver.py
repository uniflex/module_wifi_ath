import logging
import zmq
import random
import sys
import time
import wishful_upis.msgs.management_pb2 as msgMgmt
from wishful_upis.msgs.msg_helper import get_msg_type
import wishful_module

__author__ = "Piotr Gawlowicz, Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz, chwalisz}@tkn.tu-berlin.de"


@wishful_module.decorate_module_class
class Ath9kDriver(wishful_module.WishfulModule):
    def __init__(self, agentPort=None):
        super(Ath9kDriver, self).__init__(agentPort)
        self.log = logging.getLogger('ath9k_driver.main')
        self.interfaces = None

    def set_interfaces(self, interfaces):
        self.interfaces = interfaces
        pass

    @wishful_module.add_msg_callback('set_channel')
    def set_channel_test(self, channel):
        self.log.debug("ATH9K sets channel: {0}".format(channel))

        return "SET_CHANNEL_OK"
