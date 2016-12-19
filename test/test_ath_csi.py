#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import uniflex_module_wifi_ath
import pickle

'''
    Direct module test; without framework.
    Req.: Atheros WiFi
'''
if __name__ == '__main__':

    wifi = uniflex_module_wifi_ath.AthModule()

    wifi.my_start_function()

    samples = 1
    csi = wifi.get_csi(samples, False)

    print(csi.shape)
