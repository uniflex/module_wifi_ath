import logging
import random
import pickle
import os
import inspect
import subprocess
import zmq
import time
import platform
import numpy as np

import wishful_upis as upis
from wishful_agent.core import exceptions
import wishful_agent.core as wishful_module
from .ath_module import AthModule

__author__ = "Piotr Gawlowicz, Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz, zubow}@tkn.tu-berlin.de"


@wishful_module.build_module
class Ath5kModule(AthModule):
    def __init__(self):
        super(Ath5kModule, self).__init__()
        self.log = logging.getLogger('Ath5kModule')

    @wishful_module.bind_function(upis.radio.configure_radio_sensitivity)
    def configure_radio_sensitivity(self, phy_dev, **kwargs):

        '''
            Configuring the carrier receiving sensitivity of the radio.
            Req.: modprobe ath5k/9k debug=0xffffffff

            #configuration of ath5k's ANI settings
            echo "ani-off" > /sys/kernel/debug/ieee80211/phy0/ath5k/ani

            supported ani modes:
            - sens-low
            - sens-high
            - ani-off
            - ani-on
            - noise-low
            - noise-high
            - spur-low
            - spur-high
            - fir-low
            - fir-high
            - ofdm-off
            - ofdm-on
            - cck-off
            - cck-on

            Documentation from Linux Kernel:

            Adaptive Noise Immunity (ANI) controls five noise immunity parameters
            depending on the amount of interference in the environment, increasing
            or reducing sensitivity as necessary.

            The parameters are:

            - "noise immunity"
            - "spur immunity"
            - "firstep level"
            - "OFDM weak signal detection"
            - "CCK weak signal detection"

            Basically we look at the amount of ODFM and CCK timing errors we get and then
            raise or lower immunity accordingly by setting one or more of these
            parameters.
        '''
        prefix = 'ath5k'
        ani_mode = kwargs.get('ani_mode')
        self.log.info('Setting ANI sensitivity w/ = %s' % str(ani_mode))

        try:
            myfile = open('/sys/kernel/debug/ieee80211/' + phy_dev + '/' + prefix + '/ani', 'w')
            myfile.write(ani_mode)
            myfile.close()
            return True
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("Failed to configure radio sensitivity: %s" % str(e))
            raise exceptions.UPIFunctionExecutionFailedException(func_name=inspect.currentframe().f_code.co_name,
                                                                 err_msg='Failed to configure radio sensitivity: %s' + str(e))