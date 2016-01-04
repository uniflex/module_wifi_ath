import logging
import zmq
import random
import sys
import time
import wishful_upis.msgs.management_pb2 as msgMgmt
from wishful_upis.msgs.msg_helper import get_msg_type

__author__ = "Piotr Gawlowicz, Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz, chwalisz}@tkn.tu-berlin.de"


class add_msg_callback(object):
    def __init__(self, *msgTypes):
        self.msgTypes = set(msgTypes)

    def __call__(self, f):
        f._msg_types = self.msgTypes
        return f


class on_start(object):
    def __init__(self):
        self.onStart = True

    def __call__(self, f):
        f._onStart = self.onStart
        return f


class on_exit(object):
    def __init__(self):
        self.onExit = True

    def __call__(self, f):
        f._onExit = self.onExit
        return f


def decorate_module_class(module_class):
    module_class.callbacks = {}
    original_methods = module_class.__dict__.copy()
    for name, method in original_methods.iteritems():
        if hasattr(method, '_msg_types'):
            for msg_type in method._msg_types - set(original_methods):
                module_class.callbacks[msg_type] = method
    return module_class


class WishfulModule(object):
    def __init__(self, port=None):
        self.log = logging.getLogger("{module}.{name}".format(
            module=self.__class__.__module__, name=self.__class__.__name__))

        for k,v in self.callbacks.iteritems():
            print "\t",k,v.__name__

        if port:
            self.port = port
            self.log.debug("Connect to Agent on port: {0}".format(port))

            # Connect to WiSHFUL Agent
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.PAIR)
            self.socket.setsockopt(zmq.LINGER, 100)
            self.socket.connect("tcp://localhost:%s" % port)

    def process_msgs(self, msgContainer):
        assert len(msgContainer) == 3
        group = msgContainer[0]
        msgDesc = msgMgmt.MsgDesc()
        msgDesc.ParseFromString(msgContainer[1])
        msg = msgContainer[2]

        self.log.debug("ATH9k process msg: {0}::{1}".format(msgDesc.msg_type, msg))
        command = msg

        response = None
        if command in self.callbacks:
            func = getattr(self, self.callbacks[command].__name__)
            response = func(1)
        return response

    def start_receive_msgs(self, socket):
        while True:
            msgContainer = socket.recv_multipart()

            assert len(msgContainer) == 3
            group = msgContainer[0]
            msgDesc = msgMgmt.MsgDesc()
            msgDesc.ParseFromString(msgContainer[1])
            msg = msgContainer[2]

            self.log.debug("Recived msg: {0}::{1}::{2}".format(group, msgDesc.msg_type, msg))

            response = self.process_msgs(msgContainer)

            if response:
                self.log.debug("Sending response: {0}".format(response))
                socket.send_multipart(response)

    def run(self):
        self.log.debug("ath9k_driver starts".format())
        try:
            self.start_receive_msgs(self.socket)
        except KeyboardInterrupt:
            self.log.debug("ATH9k_driver exits")


@decorate_module_class
class Ath9kDriver(WishfulModule):
    def __init__(self, agentPort=None):
        super(Ath9kDriver, self).__init__(agentPort)

        self.interfaces = None

    def set_interfaces(self, interfaces):
        self.interfaces = interfaces
        pass

    @add_msg_callback('SET_CHANNEL')
    def set_channel(self, channel):
        self.log = logging.getLogger('ath9k_driver.main')
        self.log.debug("ATH9K sets channel: {0}".format(channel))

        group = "RESPONSE"
        msgDesc = msgMgmt.MsgDesc()
        msgDesc.msg_type = "ATH9K_RESPONSE"
        msg = "SET_CHANNEL_OK"
        response = [group, msgDesc.SerializeToString(), msg]

        return response
