import zmq
import random
import sys
import time
import gevent

port = "5556"

class Driver (object):
    def __init__(self):
        print "ath9k_driver"


        pass

    def startSocket(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect("tcp://localhost:%s" % port)

        self.waitForMsg()


    def waitForMsg(self):
        while True:
            msg = self.socket.recv()
            print msg
            self.socket.send("client message to server1")
            self.socket.send("client message to server2")
            time.sleep(1)

    def reciveMsg(self, msg):
        print msg