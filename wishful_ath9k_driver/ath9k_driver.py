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

class Ath9kDriver(object):
    def __init__(self, agentPort=None):
        self.log = logging.getLogger("{module}.{name}".format(
            module=self.__class__.__module__, name=self.__class__.__name__))

        self.interfaces = None

        if agentPort:
            self.port = agentPort
            self.log.debug("Connect to Agent on port: {0}".format(agentPort))

            #Connect to WiSHFUL Agent
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.PAIR)
            self.socket.connect("tcp://localhost:%s" % agentPort)


    def set_interfaces(self, interfaces):
        self.interfaces = interfaces


    def set_channel(self, channel):
        self.log = logging.getLogger('ath9k_driver.main')
        self.log.debug("ATH9K sets channel: {0}".format(channel))

        group = "RESPONSE"
        msgDesc = msgMgmt.MsgDesc()
        msgDesc.msg_type = "ATH9K_RESPONSE"
        msg = "SET_CHANNEL_OK"
        response = [group, msgDesc.SerializeToString(), msg]
        
        return  response

    def process_msgs(self, msgContainer):
        assert len(msgContainer) == 3
        group = msgContainer[0]
        msgDesc = msgMgmt.MsgDesc()
        msgDesc.ParseFromString(msgContainer[1])
        msg = msgContainer[2]

        self.log.debug("ATH9k process msg: {0}::{1}".format(msgDesc.msg_type, msg))

        command = msg

        response = None
        if msgDesc.msg_type == "RADIO" and command == "SET_CHANNEL":
            response = self.set_channel(1)

        return response

    def start_receive_msgs(self, socket):
         while True:
                msgContainer = socket.recv_multipart()

                assert len(msgContainer) == 3
                group = msgContainer[0]
                msgDesc = msgMgmt.MsgDesc()
                msgDesc.ParseFromString(msgContainer[1])
                msg = msgContainer[2]

                self.log.debug("ATH9K driver recived msg: {0}::{1}::{2}".format(group, msgDesc.msg_type, msg))

                response = self.process_msgs(msgContainer)

                if response:
                    self.log.debug("ATH9k sends response: {0}".format(response))
                    socket.send_multipart(response)


    def run(self):
        self.log.debug("ath9k_driver starts".format())
        try:
            self.start_receive_msgs(self.socket)
        except KeyboardInterrupt:
            self.log.debug("ATH9k_driver exits")