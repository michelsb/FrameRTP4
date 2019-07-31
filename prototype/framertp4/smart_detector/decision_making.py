import threading
import numpy as np
from utils.ml_model import load_model_file
from utils.rules import generate_icmp_rule,generate_tcp_rule,generate_udp_rule
from utils.convert import convert_int_to_ip
import definitions
from smart_detector.flow_stats_collector import FlowStatsCollector

class DecisionMakingModule():

    def __init__(self, core):
        self.core = core
        self.clf = load_model_file(definitions.MLMODEL_NAME)
        self.collector = FlowStatsCollector(self.core.client_driver)
        self.firstTime = True

    def connect_collector(self):
        self.collector.start_collector()

    def try_detect_new_atacks(self):
        data = self.collector.get_metrics_from_controllers()
        for controller in data:
            for switch in data[controller]:
                df = data[controller][switch]
                if not df.empty:
                    X = df.drop('proto', axis=1).drop('srcAddr', axis=1).drop('dstAddr', axis=1).drop(
                        'srcPort', axis=1).drop('dstPort', axis=1).drop('ratePktsRcvd', axis=1).drop('rateBytesRcvd', axis=1)
                    preds = self.clf.predict(X)
                    indexes = np.where(preds == 0)
                    df_attacks = df.loc[indexes[0], ["srcAddr", "dstAddr", "srcPort", "dstPort", "proto"]]
                    for index, row in df_attacks.iterrows():
                        srcAddr = convert_int_to_ip(row["srcAddr"])
                        dstAddr = convert_int_to_ip(row["dstAddr"])
                        if row["proto"] == 1:
                            table_id, rule = generate_icmp_rule(srcAddr,dstAddr)
                        elif row["proto"] == 6:
                            table_id, rule = generate_tcp_rule(srcAddr, dstAddr, row["srcPort"], row["dstPort"])
                        elif row["proto"] == 17:
                            table_id, rule = generate_udp_rule(srcAddr, dstAddr, row["srcPort"], row["dstPort"])
                        else:
                            continue
                        self.core.add_rule(table_id,rule)

        t = threading.Timer(definitions.SFCMON_READ_TIMEOUT, self.try_detect_new_atacks)
        t.daemon = True
        t.start()

    def start_decision_making(self):
        if self.firstTime:
            self.connect_collector()
            self.try_detect_new_atacks()
            #self.reset_iblt()
            self.firstTime = False