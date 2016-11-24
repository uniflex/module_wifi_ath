import logging
import inspect
import subprocess
import iptc
from pytc.TrafficControl import TrafficControl

import uniflex_module_wifi
from uniflex.core import exceptions


__author__ = "Piotr Gawlowicz, Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz, zubow}@tkn.tu-berlin.de"


class AthModule(uniflex_module_wifi.WifiModule):
    def __init__(self):
        super(AthModule, self).__init__()
        self.log = logging.getLogger('AthModule')

    def set_mac_access_parameters(self, iface, queueId, queueParams):
        '''
        Sets the MAC access parameters -> see IEEE 802.11e
        TODO: replace by Netlink
        '''
        self.log.info("ATH9K sets EDCA parameters for queue: {} on interface: {}".format(queueId, iface))

        self.log.debug("AIFS: {}".format(queueParams.getAifs()))
        self.log.debug("CwMin: {}".format(queueParams.getCwMin()))
        self.log.debug("CwMax: {}".format(queueParams.getCwMax()))
        self.log.debug("TxOp: {}".format(queueParams.getTxOp()))

        try:
            cmd_str = ('sudo iw ' + iface + ' info')
            cmd_output = subprocess.check_output(cmd_str, shell=True, stderr=subprocess.STDOUT)
            cmd_output = cmd_output.decode("utf-8")
            for item in cmd_output.split("\n"):
                if "wiphy" in item:
                    line = item.strip()

            phyId = [int(s) for s in line.split() if s.isdigit()][0]

            myfile = open('/sys/kernel/debug/ieee80211/phy'+str(phyId)+'/ath9k/txq_params', 'w')
            value = str(queueId) + " " + str(queueParams.getAifs()) + " " + str(queueParams.getCwMin()) + " " + str(queueParams.getCwMax()) + " " + str(queueParams.getTxOp())
            myfile.write(value)
            myfile.close()
            return True
        except Exception as e:
            self.log.fatal("Failed to set EDCA parameters: %s" % str(e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to set EDCA parameters: ' + str(e))

    def get_mac_access_parameters(self, iface):
        self.log.debug("ATH9K gets EDCA parameters for interface: {}".format(iface))

        try:
            cmd_str = ('sudo iw ' + iface + ' info')
            cmd_output = subprocess.check_output(cmd_str, shell=True, stderr=subprocess.STDOUT)

            for item in cmd_output.split("\n"):
                 if "wiphy" in item:
                    line = item.strip()

            phyId = [int(s) for s in line.split() if s.isdigit()][0]

            myfile = open('/sys/kernel/debug/ieee80211/phy'+str(phyId)+'/ath9k/txq_params', 'r')
            data = myfile.read()
            myfile.close()
            return data
        except Exception as e:
            self.log.fatal("Failed to get EDCA parameters: %s" % str(e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to get EDCA parameters: ' + str(e))

    def set_per_flow_tx_power(self, iface, flowId, txPower):
        self.log.debug('set_per_flow_tx_power on iface: {}'.format(iface))

        try:
            tcMgr = TrafficControl()
            markId = tcMgr.generateMark()
            self.setMarking(flowId, table="mangle", chain="POSTROUTING", markId=markId)

            cmd_str = ('sudo iw ' + iface + ' info')
            cmd_output = subprocess.check_output(cmd_str, shell=True, stderr=subprocess.STDOUT)

            for item in cmd_output.split("\n"):
                 if "wiphy" in item:
                    line = item.strip()

            phyId = [int(s) for s in line.split() if s.isdigit()][0]

            myfile = open('/sys/kernel/debug/ieee80211/phy'+str(phyId)+'/ath9k/per_flow_tx_power', 'w')
            value = str(markId) + " " + str(txPower) + " 0"
            myfile.write(value)
            myfile.close()
            return True
        except Exception as e:
            self.log.fatal("Failed to set per flow tx power: %s" % str(e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to set per flow tx power: ' + str(e))

    ''' Helper '''
    def setMarking(self, flowId, table="mangle", chain="POSTROUTING", markId=None):
        if not markId:
            tcMgr = TrafficControl()
            markId = tcMgr.generateMark()

        rule = iptc.Rule()

        if flowId.srcAddress:
            rule.src = flowId.srcAddress

        if flowId.dstAddress:
            rule.dst = flowId.dstAddress

        if flowId.prot:
            rule.protocol = flowId.prot
            match = iptc.Match(rule, flowId.prot)

            if flowId.srcPort:
                match.sport = flowId.srcPort

            if flowId.dstPort:
                match.dport = flowId.dstPort

            rule.add_match(match)

        target = iptc.Target(rule, "MARK")
        target.set_mark = str(markId)
        rule.target = target
        chain = iptc.Chain(iptc.Table(table), chain)
        chain.insert_rule(rule)

    def clean_per_flow_tx_power_table(self, iface):
        self.log.debug('clean_per_flow_tx_power_table on iface: {}'.format(iface))

        try:
            cmd_str = ('sudo iw ' + iface + ' info')
            cmd_output = subprocess.check_output(cmd_str, shell=True, stderr=subprocess.STDOUT)

            for item in cmd_output.split("\n"):
                 if "wiphy" in item:
                    line = item.strip()

            phyId = [int(s) for s in line.split() if s.isdigit()][0]

            myfile = open('/sys/kernel/debug/ieee80211/phy'+str(phyId)+'/ath9k/per_flow_tx_power', 'w')
            value = "0 0 0"
            myfile.write(value)
            myfile.close()
            return True
        except Exception as e:
            self.log.fatal("Failed to clean per flow tx power: %s" % str(e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to clean per flow tx power: ' + str(e))

    def get_per_flow_tx_power_table(self, iface):
        self.log.debug('get_per_flow_tx_power_table on iface: {}'.format(iface))

        try:
            cmd_str = ('sudo iw ' + iface + ' info')
            cmd_output = subprocess.check_output(cmd_str, shell=True, stderr=subprocess.STDOUT)

            for item in cmd_output.split("\n"):
                 if "wiphy" in item:
                    line = item.strip()

            phyId = [int(s) for s in line.split() if s.isdigit()][0]

            myfile = open('/sys/kernel/debug/ieee80211/phy'+str(phyId)+'/ath9k/per_flow_tx_power', 'r')
            data = myfile.read()
            myfile.close()
            return data
        except Exception as e:
            self.log.fatal("Failed to get per flow tx power: %s" % str(e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to get per flow tx power: ' + str(e))

    def get_noise(self):
        self.log.error('Get noise function not yet implemented')
        raise exceptions.UnsupportedFunctionException(
            func_name=inspect.currentframe().f_code.co_name,
            conn_module='AthModule')

    def get_airtime_utilization(self):
        self.log.error('Get artime utilization function not yet implemented')
        raise exceptions.UnsupportedFunctionException(
            func_name=inspect.currentframe().f_code.co_name,
            conn_module='AthModule')
