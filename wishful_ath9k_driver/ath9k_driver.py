import logging
import wishful_module
import wishful_upis as upis


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

    @wishful_module.bind_function(upis.radio.set_channel)
    def set_channel(self, channel):
        self.log.debug("ATH9K sets channel: {} on interface: {}".format(channel, self.interface))

        return "SET_CHANNEL_OK"
