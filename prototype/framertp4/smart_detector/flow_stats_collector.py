import time
import copy
import threading
import pandas as pd
import definitions
from smart_detector.sfcmoniblt_processor import SFCMonIBLTProcessor

class FlowStatsCollector():
    def __init__(self,client_driver):
        self.client_driver = client_driver
        self.iblt_processor = SFCMonIBLTProcessor()
        self.new_results = {}
        self.old_results = {}
        self.firstTime = True

    def generate_bi_flows(self, df):
        df = df.sort_values(by='first_seen')
        bi_flows = {}
        for index, row in df.iterrows():
            entry1 = (row["srcAddr"], row["dstAddr"], row["srcPort"], row["dstPort"], row["proto"])
            entry2 = (row["dstAddr"], row["srcAddr"], row["dstPort"], row["srcPort"], row["proto"])
            if entry1 not in bi_flows:
                if entry2 not in bi_flows:
                    bi_flows[entry1]={"numPktsSnt":row["ctr_pkts"],"numBytesSnt":row["ctr_bytes"],"numPktsRcvd":0,'numBytesRcvd':0}
                else:
                    bi_flows[entry2]["numPktsRcvd"] = row["ctr_pkts"]
                    bi_flows[entry2]["numBytesRcvd"] = row["ctr_bytes"]
        return bi_flows

    def collect_iblt_from_controllers(self):
        response = {}
        data = self.client_driver.readSFCMon()
        for controller in data:
            response[controller] = {}
            for switch in data[controller]:
                timestamp = data[controller][switch]["timestamp"]
                del data[controller][switch]["timestamp"]
                is_created, columns = self.iblt_processor.create_iblt(data[controller][switch])
                if not is_created:
                    raise Exception('The following fields are not in data structure: ' + str(columns))
                uni_flows_df = self.iblt_processor.listing()
                bi_flows_df = self.generate_bi_flows(uni_flows_df)
                response[controller][switch] = {"timestamp":timestamp,"data":bi_flows_df}
        self.new_results = response

    def reset_iblt_from_controllers(self):
        self.client_driver.resetSFCMon()
        time.sleep(2)
        t = threading.Timer(definitions.SFCMON_RESET_TIMEOUT, self.reset_iblt_from_controllers)
        t.daemon = True
        t.start()


    def calculate_metrics(self):
        response = {}
        for controller in self.new_results:
            if controller in self.old_results:
                response[controller] = {}
                for switch in self.new_results[controller]:
                    if switch in self.old_results[controller]:
                        o_timestamp = self.old_results[controller][switch]["timestamp"]
                        n_timestamp = self.new_results[controller][switch]["timestamp"]
                        o_data = self.old_results[controller][switch]["data"]
                        n_data = self.new_results[controller][switch]["data"]
                        interval = n_timestamp - o_timestamp
                        stats_flows = []

                        for flow in n_data:
                            if flow in o_data:
                                srcAddr = flow[0]
                                dstAddr = flow[1]
                                srcPort = flow[2]
                                dstPort = flow[3]
                                proto = flow[4]

                                old_numPktsSnt = o_data[flow]["numPktsSnt"]
                                old_numBytesSnt = o_data[flow]["numBytesSnt"]
                                old_numPktsRcvd = o_data[flow]["numPktsRcvd"]
                                old_numBytesRcvd = o_data[flow]["numBytesRcvd"]

                                new_numPktsSnt = n_data[flow]["numPktsSnt"]
                                new_numBytesSnt = n_data[flow]["numBytesSnt"]
                                new_numPktsRcvd = n_data[flow]["numPktsRcvd"]
                                new_numBytesRcvd = n_data[flow]["numBytesRcvd"]

                                ratePktsSnt = (new_numPktsSnt - old_numPktsSnt) / (interval * 1.0)
                                rateBytesSnt = (new_numBytesSnt - old_numBytesSnt) / (interval * 1.0)
                                ratePktsRcvd = (new_numPktsRcvd - old_numPktsRcvd) / (interval * 1.0)
                                rateBytesRcvd = (new_numBytesRcvd - old_numBytesRcvd) / (interval * 1.0)

                                data = [srcAddr, dstAddr, srcPort, dstPort, proto,
                                        new_numPktsSnt, new_numBytesSnt, new_numPktsRcvd, new_numBytesRcvd,
                                        ratePktsSnt, rateBytesSnt, ratePktsRcvd, rateBytesRcvd]
                                stats_flows.append(data)
                    response[controller][switch] = pd.DataFrame(stats_flows,columns=["srcAddr","dstAddr","srcPort","dstPort","proto",
                                                     "numPktsSnt", "numBytesSnt", "numPktsRcvd", "numBytesRcvd",
                                                     "ratePktsSnt", "rateBytesSnt", "ratePktsRcvd", "rateBytesRcvd"])
        return response

    def get_metrics_from_controllers(self):
        self.collect_iblt_from_controllers()
        response = self.calculate_metrics()
        self.old_results = copy.deepcopy(self.new_results)
        return response

    def connect(self):
        self.collect_iblt_from_controllers()
        self.old_results = copy.deepcopy(self.new_results)

    def start_collector(self):
        if self.firstTime:
            self.reset_iblt_from_controllers()
            self.connect()
            time.sleep(definitions.SFCMON_READ_TIMEOUT)
            self.get_metrics_from_controllers()
            self.firstTime = False