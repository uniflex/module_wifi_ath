import logging
import wishful_module
import wishful_upis as upis
import edca #<----!!!!! Important to include it here; otherwise cannot be pickled!!!!


__author__ = "Piotr Gawlowicz, Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz, chwalisz}@tkn.tu-berlin.de"


@wishful_module.build_module
class Ath9kDriver(wishful_module.WishfulModule):
    def __init__(self, agentPort=None):
        super(Ath9kDriver, self).__init__(agentPort)
        self.log = logging.getLogger('ath9k_module.main')
        self.interface = "wlan0"
        self.channel = 1
        self.power = 1


    @wishful_module.bind_function(upis.radio.set_channel)
    def set_channel(self, channel):
        self.log.debug("ATH9K sets channel: {} on interface: {}".format(channel, self.interface))
        self.channel = channel
        return "SET_CHANNEL_OK"


    @wishful_module.bind_function(upis.radio.get_channel)
    def get_channel(self):
        self.log.debug("Gets channel of interface: {}".format(self.interface))
        return "CHANNEL_{}".format(self.channel)


    @wishful_module.bind_function(upis.radio.set_power)
    def set_power(self, power):
        self.log.debug("ATH9K sets power: {} on interface: {}".format(power, self.interface))
        self.power = power
        return "SET_POWER_OK_value_{}".format(power)


    @wishful_module.bind_function(upis.radio.get_power)
    def get_power(self):
        self.log.debug("ATH9K gets power on interface: {}".format(self.interface))
        return "POWER_{}".format(self.power)


    @wishful_module.bind_function(upis.radio.setEdcaParameters)
    def setEdcaParameters(self, queueId, queueParams):
        self.log.debug("ATH9K sets EDCA parameters for queue: {} on interface: {}".format(queueId, self.interface))

        print "Setting EDCA parameters for queue: {}".format(queueId)
        print "AIFS: {}".format(queueParams.getAifs())
        print "CwMin: {}".format(queueParams.getCwMin())
        print "CwMax: {}".format(queueParams.getCwMax())
        print "TxOp: {}".format(queueParams.getTxOp())

        return "EDCA_OK"

