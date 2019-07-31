#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import csv, os
import pandas as pd
import numpy as np
import datetime
from countminsketch import CountMinSketch

from definitions import DATASET_DIR, array_bound, flow_id, array_time_window, array_pkts_to_start
from util import calculate_metrics, calculate_metrics_bot, create_directory, delete_directory

import time

CTU13_DIR = os.path.join(DATASET_DIR, 'ctu-13')
CTU13_1_DIR = os.path.join(CTU13_DIR, '1')
CTU13_2_DIR = os.path.join(CTU13_DIR, '2')
CTU13_3_DIR = os.path.join(CTU13_DIR, '3')
CTU13_4_DIR = os.path.join(CTU13_DIR, '4')
CTU13_5_DIR = os.path.join(CTU13_DIR, '5')
CTU13_6_DIR = os.path.join(CTU13_DIR, '6')
CTU13_7_DIR = os.path.join(CTU13_DIR, '7')
CTU13_8_DIR = os.path.join(CTU13_DIR, '8')
CTU13_9_DIR = os.path.join(CTU13_DIR, '9')
CTU13_10_DIR = os.path.join(CTU13_DIR, '10')
CTU13_11_DIR = os.path.join(CTU13_DIR, '11')
CTU13_12_DIR = os.path.join(CTU13_DIR, '12')
CTU13_13_DIR = os.path.join(CTU13_DIR, '13')

CTU13_1_LABELLED_FILE = os.path.join(CTU13_1_DIR, 'capture20110810.binetflow')
CTU13_2_LABELLED_FILE = os.path.join(CTU13_2_DIR, 'capture20110811.binetflow')
CTU13_3_LABELLED_FILE = os.path.join(CTU13_3_DIR, 'capture20110812.binetflow')
CTU13_4_LABELLED_FILE = os.path.join(CTU13_4_DIR, 'capture20110815.binetflow')
CTU13_5_LABELLED_FILE = os.path.join(CTU13_5_DIR, 'capture20110815-2.binetflow')
CTU13_6_LABELLED_FILE = os.path.join(CTU13_6_DIR, 'capture20110816.binetflow')
CTU13_7_LABELLED_FILE = os.path.join(CTU13_7_DIR, 'capture20110816-2.binetflow')
CTU13_8_LABELLED_FILE = os.path.join(CTU13_8_DIR, 'capture20110816-3.binetflow')
CTU13_9_LABELLED_FILE = os.path.join(CTU13_9_DIR, 'capture20110817.binetflow')
CTU13_10_LABELLED_FILE = os.path.join(CTU13_10_DIR, 'capture20110818.binetflow')
CTU13_11_LABELLED_FILE = os.path.join(CTU13_11_DIR, 'capture20110818-2.binetflow')
CTU13_12_LABELLED_FILE = os.path.join(CTU13_12_DIR, 'capture20110819.binetflow')
CTU13_13_LABELLED_FILE = os.path.join(CTU13_13_DIR, 'capture20110815-3.binetflow')

CTU13_1_FROMPCAP_FILE = os.path.join(CTU13_1_DIR, '1-capture.csv')
CTU13_2_FROMPCAP_FILE = os.path.join(CTU13_2_DIR, '2-capture.csv')
CTU13_3_FROMPCAP_FILE = os.path.join(CTU13_3_DIR, '3-capture.csv')
CTU13_4_FROMPCAP_FILE = os.path.join(CTU13_4_DIR, '4-capture.csv')
CTU13_5_FROMPCAP_FILE = os.path.join(CTU13_5_DIR, '5-capture.csv')
CTU13_6_FROMPCAP_FILE = os.path.join(CTU13_6_DIR, '6-capture.csv')
CTU13_7_FROMPCAP_FILE = os.path.join(CTU13_7_DIR, '7-capture.csv')
CTU13_8_FROMPCAP_FILE = os.path.join(CTU13_8_DIR, '8-capture.csv')
CTU13_9_FROMPCAP_FILE = os.path.join(CTU13_9_DIR, '9-capture.csv')
CTU13_10_FROMPCAP_FILE = os.path.join(CTU13_10_DIR, '10-capture.csv')
CTU13_11_FROMPCAP_FILE = os.path.join(CTU13_11_DIR, '11-capture.csv')
CTU13_12_FROMPCAP_FILE = os.path.join(CTU13_12_DIR, '12-capture.csv')
CTU13_13_FROMPCAP_FILE = os.path.join(CTU13_13_DIR, '13-capture.csv')

list_labelled_files = [CTU13_1_LABELLED_FILE,CTU13_2_LABELLED_FILE,CTU13_3_LABELLED_FILE,CTU13_4_LABELLED_FILE,
                       CTU13_5_LABELLED_FILE,CTU13_6_LABELLED_FILE,CTU13_7_LABELLED_FILE,CTU13_8_LABELLED_FILE,
                       CTU13_9_LABELLED_FILE,CTU13_10_LABELLED_FILE,CTU13_11_LABELLED_FILE,CTU13_12_LABELLED_FILE,
                       CTU13_13_LABELLED_FILE]

list_frompcap_files = [CTU13_1_FROMPCAP_FILE,CTU13_2_FROMPCAP_FILE,CTU13_3_FROMPCAP_FILE,CTU13_4_FROMPCAP_FILE,
                       CTU13_5_FROMPCAP_FILE,CTU13_6_FROMPCAP_FILE,CTU13_7_FROMPCAP_FILE,CTU13_8_FROMPCAP_FILE,
                       CTU13_9_FROMPCAP_FILE,CTU13_10_FROMPCAP_FILE,CTU13_11_FROMPCAP_FILE,CTU13_12_FROMPCAP_FILE,
                       CTU13_13_FROMPCAP_FILE]

file_indexes = [0,1,2,4,5,6,7,8,10,12]
#file_indexes = [2,4,5,6,7,8,10,11,12]
#file_indexes = [12]

def read_labelled_file(file_path):
    print("# " + str(datetime.datetime.now()) + " - Reading CSV...")
    df = pd.read_csv(file_path, sep=',', header=0)
    print("# " + str(datetime.datetime.now()) + " - CSV loaded inside a dataframe...")
    return df

def read_pcap_file(file_path):
    print("# " + str(datetime.datetime.now()) + " - Reading CSV...")

    dateparse = lambda x: datetime.datetime(int(x[8:12]),8,int(x[4:6]),int(x[13:15]),int(x[16:18]),int(x[19:21]),int(x[22:28]))
    headers = ["datetime","SrcIP","DstIP","Proto","SrcPort","DstPort","aux_SrcPort","aux_DstPort","Size"]
    dtypes = {"Proto":np.uint8,"SrcPort":np.float32,"DstPort":np.float32,"aux_SrcPort":np.float32,"aux_DstPort":np.float32,"Size":np.uint16}
    iter_csv = pd.read_csv(file_path, sep=';', header=None, chunksize=10000000,
                           names=headers, dtype=dtypes, parse_dates=['datetime'], date_parser=dateparse)

    df = pd.concat([chunk[chunk["Proto"] != 1] for chunk in iter_csv])
    df.drop("Size", axis=1, inplace=True)

    print("# " + str(datetime.datetime.now()) + " - CSV loaded inside a dataframe...")

    print("# " + str(datetime.datetime.now()) + " - Generating DataFrame...")

    df["SrcPort"].fillna(df["aux_SrcPort"], inplace=True)
    df["DstPort"].fillna(df["aux_DstPort"], inplace=True)
    df.drop("aux_SrcPort", axis=1, inplace=True)
    df.drop("aux_DstPort", axis=1, inplace=True)
    df["SrcPort"] = df["SrcPort"].astype(np.uint16)
    df["DstPort"] = df["DstPort"].astype(np.uint16)
    df.set_index(pd.DatetimeIndex(df["datetime"]),inplace=True)
    df.drop("datetime", axis=1, inplace=True)

    print("# " + str(datetime.datetime.now()) + " - DataFrame generated...")

    return df

def generate_botnet_baseline(df):
    print("# " + str(datetime.datetime.now()) + " - Generating Botnet Baseline...")
    baseline = {}
    filtered_df = df[df["Label"].str.contains("Botnet")]
    filtered_df = filtered_df[(filtered_df["Proto"] == "tcp") | (filtered_df["Proto"] == "udp")]
    filtered_df["Proto2"] = np.where(filtered_df["Proto"] == "udp", 17, 6)
    filtered_df["Sport"] = filtered_df["Sport"].astype(int)
    filtered_df["Dport"] = filtered_df["Dport"].astype(int)
    five_tuple_df = filtered_df[["SrcAddr", "DstAddr", "Sport", "Dport", "Proto2"]].apply(tuple, axis=1)
    baseline["bot-srcips"] = set(filtered_df["SrcAddr"].tolist())
    baseline["bot-5-tuples"] = set(five_tuple_df.tolist())
    print("# " + str(datetime.datetime.now()) + " - Botnet Baseline generated...")
    return baseline

def generate_baseline(df,bound):
    print("# " + str(datetime.datetime.now()) + " - Generating HH Baseline...")
    baseline = {}
    num_packets = df.shape[0]
    hh_threshold_packets = num_packets * bound
    df_flows = df.groupby(flow_id)
    df_flows_stats = df_flows.size().reset_index(name='counts')

    is_hh_packets = df_flows_stats["counts"] >= hh_threshold_packets
    df_hh_flows_packets = df_flows_stats[is_hh_packets]
    df_not_hh_flows_packets = df_flows_stats[~is_hh_packets]

    # SrcIP
    baseline["packets"] = set(df_hh_flows_packets["SrcIP"].tolist())
    baseline["tn_packets"] = set(df_not_hh_flows_packets["SrcIP"].tolist())

    # 5-tuples
    five_tuple_df = df_hh_flows_packets[["SrcIP", "DstIP", "SrcPort", "DstPort", "Proto"]].apply(tuple, axis=1)
    baseline["5t_packets"] = set(five_tuple_df.tolist())
    five_tuple_df = df_not_hh_flows_packets[["SrcIP", "DstIP", "SrcPort", "DstPort", "Proto"]].apply(tuple, axis=1)
    baseline["5t_tn_packets"] = set(five_tuple_df.tolist())
    print("# " + str(datetime.datetime.now()) + " - HH Baseline generated...")
    return baseline

def simulate_rtp4mon(df,bound,pkts_to_start):
    print("# " + str(datetime.datetime.now()) + " - Begin simulation RTP4Mon...")
    results = {"packets": set(), "5t_packets": set()}
    sketch_packets = CountMinSketch(5436, 5)  # table size=1000, hash functions=10
    count_packets = 0
    for row in zip(df["SrcIP"],df["DstIP"],df["SrcPort"],df["DstPort"],df["Proto"]):
        flow_id = row[0]
        five_flow_id = row
        sketch_packets.add(flow_id)
        count_packets += 1
        if count_packets > pkts_to_start:
            hh_threshold_packets = count_packets * bound
            if sketch_packets[flow_id] > hh_threshold_packets:
                results["packets"].add(flow_id)
                results["5t_packets"].add(five_flow_id)
    print("# " + str(datetime.datetime.now()) + " - End simulation RTP4Mon...")
    return results

def generate_hh_stats(baseline_hh,results):
    TP_hh = len(results["packets"] & baseline_hh["packets"])  # The flow was reported as HH and it is HH
    TN_hh = len(baseline_hh["tn_packets"] - results[
        "packets"])  # The flow was not reported as HH and it is not HH
    FP_hh = len(
        results["packets"] - baseline_hh["packets"])  # The flow was reported as HH, but it is not HH.
    FN_hh = len(
        baseline_hh["packets"] - results["packets"])  # The flow was not reported as HH, but it is HH
    metrics_hh = calculate_metrics(TP_hh, TN_hh, FP_hh, FN_hh)

    stats_hh = [TP_hh, TN_hh, FP_hh, FN_hh,
             metrics_hh["TPR"], metrics_hh["TNR"], metrics_hh["FPR"], metrics_hh["FNR"],
             metrics_hh["precision"], metrics_hh["accuracy"], metrics_hh["f1_score"]]

    return stats_hh

def generate_bot_stats(baseline_bot,results_bot_5tflows):

    # The flow was reported as HH and it is Botnet
    TP_bot = len(results_bot_5tflows & baseline_bot["bot-5-tuples"])

    # The flow was not reported as HH and it is not Botnet
    #TN_bot = len((baseline_hh["5t_packets"] | baseline_hh["5t_tn_packets"]) - results["5t_packets"] - baseline_bot["bot-5-tuples"])
    # The flow was reported as HH, but it is not Botnet.
    #FP_bot = len(results["5t_packets"] - baseline_bot["bot-5-tuples"])

    # The flow was not reported as HH, but it is Botnet
    FN_bot = len(baseline_bot["bot-5-tuples"] - results_bot_5tflows)
    metrics_bot = calculate_metrics_bot(TP_bot, FN_bot)

    stats_bot = [TP_bot, FN_bot,
                metrics_bot["TPR"]]

    return stats_bot

def do_simulations():
    delete_directory("./results")
    create_directory("./results")

    for index in file_indexes:
        print("#################### PROCESSING SCENARIO "+str(index)+" #########################")
        path_files = "./results/scenario-"+str(index)
        create_directory(path_files)

        print ("#### Reading labbeled file: " + list_labelled_files[index])
        df = read_labelled_file(list_labelled_files[index])
        print ("#### Generating baseline labbeled file: " + list_labelled_files[index])
        baseline_bot = generate_botnet_baseline(df)
        num_bot_5tflows = len(baseline_bot["bot-5-tuples"])

        print ("#### Reading pcap's csv file: " + list_frompcap_files[index])
        df = read_pcap_file(list_frompcap_files[index])

        #baseline_hh = {}
        print ("#### Generating baseline pcap's csv file: " + list_labelled_files[index])
        for time_window in array_time_window:
            out_file_hh = csv.writer(
                open(path_files + "/hh_stats_f" + str(index) + "_w" + str(time_window) + ".csv", "wb"),
                delimiter=';', quoting=csv.QUOTE_ALL)
            columns = ["index_chunk", "bound",
                       "total_num_flows", "total_num_hh_flows", "total_num_5tflows", "total_num_hh_5tflows",
                       "pkts_to_start_hhtests", "TP", "TN", "FP", "FN",
                       "TPR (Recall)", "TNR", "FPR", "FNR",
                       "Precision", "Accuracy", "F1_Score"]
            out_file_hh.writerow(columns)

            out_file_bot = csv.writer(
                open(path_files + "/bot_stats_f" + str(index) + "_w" + str(time_window) + ".csv", "wb"),
                delimiter=';', quoting=csv.QUOTE_ALL)
            columns = ["bound", "total_num_bot_5tflows", "pkts_to_start_hhtests", "TP", "FN", "TPR (Recall)"]
            out_file_bot.writerow(columns)

            time = str(time_window) + 's'
            chunks = df.groupby(pd.Grouper(freq=time))
            index_chunk = 1
            results_bot_5tflows = {}
            for name, c in chunks:
                for bound in array_bound:
                    print "### Time Window: " + str(time_window) + " - Time Slot: " + str(index_chunk) + " - Bound: " + str(bound)

                    if str(bound) not in results_bot_5tflows:
                        results_bot_5tflows[str(bound)] = {}

                    baseline_hh = generate_baseline(c, bound)
                    data = [index_chunk,bound,
                            len(baseline_hh["packets"]) + len(baseline_hh["tn_packets"]),
                            len(baseline_hh["packets"]),
                            len(baseline_hh["5t_packets"]) + len(baseline_hh["5t_tn_packets"]),
                            len(baseline_hh["5t_packets"])]

                    data_pkts_to_start = [[]]
                    data_hh_stats = [[],[],[],[],[],[],[],[],[],[],[]]
                    for pkts_to_start in array_pkts_to_start:
                        print "## Packets to Start HH Tests: " + str(pkts_to_start)

                        if str(pkts_to_start) not in results_bot_5tflows[str(bound)]:
                            results_bot_5tflows[str(bound)][str(pkts_to_start)] = set()

                        data_pkts_to_start[0].append(pkts_to_start)
                        results = simulate_rtp4mon(c,bound,pkts_to_start)
                        results_bot_5tflows[str(bound)][str(pkts_to_start)] = results_bot_5tflows[str(bound)][str(pkts_to_start)] | results["5t_packets"]
                        hh_stats = generate_hh_stats(baseline_hh,results)
                        for i in range(0,len(data_hh_stats)):
                            data_hh_stats[i].append(hh_stats[i])

                    data = data + data_pkts_to_start + data_hh_stats
                    out_file_hh.writerow(data)
                index_chunk+=1

            for bound in array_bound:
                data_pkts_to_start = [[]]
                data_bot_stats = [[], [], []]
                data = [bound,num_bot_5tflows]
                for pkts_to_start in array_pkts_to_start:
                    data_pkts_to_start[0].append(pkts_to_start)
                    bot_stats = generate_bot_stats(baseline_bot, results_bot_5tflows[str(bound)][str(pkts_to_start)])
                    for i in range(0, len(data_bot_stats)):
                        data_bot_stats[i].append(bot_stats[i])
                data = data + data_pkts_to_start + data_bot_stats
                out_file_bot.writerow(data)


def do_test():
    for index in file_indexes:
        print("#################### PROCESSING SCENARIO "+str(index)+" #########################")
        print ("#### Reading labbeled file: " + list_labelled_files[index])
        df = read_labelled_file(list_labelled_files[index])
        print ("#### Generating baseline labbeled file: " + list_labelled_files[index])
        baseline_bot = generate_botnet_baseline(df)




#perform_experiments()
#test_files()

# df = read_pcap_file(CTU13_1_FROMPCAP_FILE)
# time.sleep(5)
# df_flows_stats = generate_baseline(df,0.0001)
#
# print df_flows_stats
do_simulations()
#do_test()

