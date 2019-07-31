#!/usr/bin/env python2

import pandas as pd
import numpy as np
import datetime, time, csv
from util import create_directory, delete_directory
from rtp4rules.rtp4rules_manager import generate_flows_with_wildcards
import matplotlib.pyplot as plt

# - DoS attacks made are:
# ICMP flood, land, estoa, smurf, flood of SYN packets, teardrop and flood of UDP packets.
# - On the other hand, port scanning type attacks are:
# TCP SYN scan, TCP connect scan, SCTP INIT scan, Null scan, FIN scan, Xmas scan, TCP ACK scan,
# TCP Window scan e TCP Maimon scan.
#csv_files = ["icmp-flood-hping3_flows.csv", "land_flows.csv", "nestea_flows.csv", "probe_flows.csv", "punk_flows.csv",
#             "smurf_flows.csv", "syn-flood-hping3-sem-pfring-filtrado_flows.csv", "syn-flood_flows.csv",
#             "teardrop_flows.csv", "udp_flood-filtrado_flows.csv"]
#
# csv_files = ["icmp-flood-hping3.csv",
#              "land.csv",
#              "nestea.csv",
#              "probe.csv",
#              "punk.csv",
#              "smurf.csv",
#              "syn-flood-hping3-sem-pfring-filtrado.csv",
#              "syn-flood.csv",
#              "teardrop.csv",
#              "udp_flood-filtrado.csv"]

# csv_files = ["land.csv",
#              "nestea.csv",
#              "probe.csv",
#              "punk.csv",
#              "syn-flood-hping3-sem-pfring-filtrado.csv",
#              "syn-flood.csv",
#              "teardrop.csv",
#              "udp_flood-filtrado.csv"]

csv_files = ["probe.csv"]

#csv_files = ["punk.csv"]

def read_csv_files():
    dfs = {}
    dateparse = lambda x: datetime.datetime(int(x[8:12]), 8, int(x[4:6]), int(x[13:15]), int(x[16:18]), int(x[19:21]),
                                            int(x[22:28]))
    headers = ["datetime", "SrcIP", "DstIP", "Proto", "SrcPort", "DstPort", "aux_SrcPort", "aux_DstPort", "Size"]
    dtypes = {"Proto": np.uint8, "SrcPort": np.float32, "DstPort": np.float32, "aux_SrcPort": np.float32,
              "aux_DstPort": np.float32, "Size": np.uint16}

    print("### " + str(datetime.datetime.now()) + " - Reading CSVs...")

    for file in csv_files:
        print("## " + str(datetime.datetime.now()) + " - Reading CSV: " + file)
        iter_csv = pd.read_csv("csv/" + file, sep=';', header=None, chunksize=10000,
                           names=headers, dtype=dtypes, parse_dates=['datetime'], date_parser=dateparse)

        df = pd.concat([chunk[chunk["Proto"] != 1] for chunk in iter_csv])
        df.drop("datetime", axis=1, inplace=True)
        df.drop("Size", axis=1, inplace=True)
        print("# " + str(datetime.datetime.now()) + " - CSV loaded inside a dataframe...")

        print("# " + str(datetime.datetime.now()) + " - Formatting DataFrame...")

        df["SrcPort"].fillna(df["aux_SrcPort"], inplace=True)
        df["DstPort"].fillna(df["aux_DstPort"], inplace=True)
        df.drop("aux_SrcPort", axis=1, inplace=True)
        df.drop("aux_DstPort", axis=1, inplace=True)
        df["SrcPort"] = df["SrcPort"].astype(np.uint16)
        df["DstPort"] = df["DstPort"].astype(np.uint16)

        df = df.drop_duplicates()
        print("# " + str(datetime.datetime.now()) + " - DataFrame formatted...")
        dfs[file] = df
    return dfs


# def read_csv_files():
#     dfs = {}
#     dateparse = lambda x: datetime.datetime(int(x[8:12]), 8, int(x[4:6]), int(x[13:15]), int(x[16:18]), int(x[19:21]),
#                                             int(x[22:28]))
#     headers = ["datetime", "SrcIP", "DstIP", "Proto", "SrcPort", "DstPort", "aux_SrcPort", "aux_DstPort", "Size"]
#     dtypes = {"Proto": np.uint8, "SrcPort": np.float32, "DstPort": np.float32, "aux_SrcPort": np.float32,
#               "aux_DstPort": np.float32, "Size": np.uint16}
#
#     print("### " + str(datetime.datetime.now()) + " - Reading CSVs...")
#
#     for file in csv_files:
#         print("## " + str(datetime.datetime.now()) + " - Reading CSV: " + file)
#         iter_csv = pd.read_csv("csv/" + file, sep=';', header=None, chunksize=10000,
#                            names=headers, dtype=dtypes, parse_dates=['datetime'], date_parser=dateparse)
#
#         df = pd.concat([chunk[chunk["Proto"] != 1] for chunk in iter_csv])
#         df.drop("datetime", axis=1, inplace=True)
#         df.drop("DstIP", axis=1, inplace=True)
#         df.drop("DstPort", axis=1, inplace=True)
#         df.drop("aux_DstPort", axis=1, inplace=True)
#         df.drop("Size", axis=1, inplace=True)
#         print("# " + str(datetime.datetime.now()) + " - CSV loaded inside a dataframe...")
#
#         print("# " + str(datetime.datetime.now()) + " - Formatting DataFrame...")
#
#         df["SrcPort"].fillna(df["aux_SrcPort"], inplace=True)
#         df.drop("aux_SrcPort", axis=1, inplace=True)
#         df["SrcPort"] = df["SrcPort"].astype(np.uint16)
#
#         df = df.drop_duplicates()
#         print("# " + str(datetime.datetime.now()) + " - DataFrame formatted...")
#         dfs[file] = df
#     return dfs

def generate_full_df (dfs):
    dfs_total = []
    for key in dfs:
        dfs_total.append(dfs[key])

    df = pd.concat(dfs_total)
    dfs["full"] = df.drop_duplicates()

    return dfs

def generate_stats_wildcards (dfs):
    print("### " + str(datetime.datetime.now()) + " - Generating Stats...")

    cols = [
        ("SrcIP","ip"),
        ("DstIP", "ip"),
        ("SrcPort","port"),
        ("DstPort", "port")
    ]

    columns_filter = ["SrcIP", "DstIP", "SrcPort", "DstPort"]

    # cols = [
    #     ("SrcIP", "ip"),
    #     ("SrcPort", "port")
    # ]
    #
    # columns_filter = ["SrcIP", "SrcPort"]

    delete_directory("./wild_results")
    create_directory("./wild_results")
    path = "./wild_results"
    out_file = csv.writer(open(path+"/wild_flows_file.csv", "w"), delimiter=',', quoting=csv.QUOTE_ALL)
    columns = ["file_name", "total_tcp_flows", "total_tcp_wildcard_rules", "tcp_duration", "total_udp_flows", "total_udp_wildcard_rules", "udp_duration"]
    out_file.writerow(columns)

    for key in dfs:

        df = dfs[key]

        if (key == "probe.csv"):
            tcp_flows = df[(df["Proto"] == 6) & (df["SrcIP"] == "146.164.69.175")][columns_filter]
            udp_flows = df[(df["Proto"] == 17) & (df["SrcIP"] == "146.164.69.175")][columns_filter]
        elif (key == "syn-flood.csv"):
            tcp_flows = df[(df["Proto"] == 6) & (df["SrcIP"] == "228.226.152.83")][columns_filter]
            udp_flows = df[(df["Proto"] == 17) & (df["SrcIP"] == "228.226.152.83")][columns_filter]
        elif (key == "land.csv"):
            tcp_flows = df[(df["Proto"] == 6) & (df["SrcIP"] == "10.10.10.3")][columns_filter]
            udp_flows = df[(df["Proto"] == 17) & (df["SrcIP"] == "10.10.10.3")][columns_filter]
        else:
            tcp_flows = df[(df["Proto"] == 6) & (df["SrcIP"] == "10.10.10.2")][columns_filter]
            udp_flows = df[(df["Proto"] == 17) & (df["SrcIP"] == "10.10.10.2")][columns_filter]

        total_tcp_flows = tcp_flows.shape[0]
        total_udp_flows = udp_flows.shape[0]

        tcp_wildcard_rules = 0
        tcp_duration = 0
        if total_tcp_flows > 0:
            print("# " + str(datetime.datetime.now()) + " - Calculating TCP Wildcard Rules: " + key)
            start = time.time()
            generate_flows_with_wildcards(tcp_flows, cols, None, 0)
            tcp_flows = tcp_flows.drop_duplicates()
            end = time.time()
            tcp_duration = end - start
            tcp_wildcard_rules = tcp_flows.shape[0]
            print("# " + str(datetime.datetime.now()) + " - TCP Wildcard Rules Generated: " + key)

        udp_wildcard_rules = 0
        udp_duration = 0
        if total_udp_flows > 0:
            print("# " + str(datetime.datetime.now()) + " - Calculating UDP Wildcard Rules: " + key)
            start = time.time()
            generate_flows_with_wildcards(udp_flows, cols, None, 0)
            udp_flows = udp_flows.drop_duplicates()
            end = time.time()
            udp_duration = end - start
            udp_wildcard_rules = udp_flows.shape[0]
            print("# " + str(datetime.datetime.now()) + " - UDP Wildcard Rules Generated: " + key)

        data = [key,total_tcp_flows,tcp_wildcard_rules,tcp_duration,total_udp_flows,udp_wildcard_rules,udp_duration]
        out_file.writerow(data)

    print("### " + str(datetime.datetime.now()) + " - Stats Generated...")

def generate_eda (dfs):
    print("### " + str(datetime.datetime.now()) + " - Generating Stats...")

    delete_directory("./eda_results")
    create_directory("./eda_results")
    path = "./eda_results"
    out_file = csv.writer(open(path+"/eda_flows_file.csv", "w"), delimiter=',', quoting=csv.QUOTE_ALL)
    columns = ["file_name", "proto","total_flows", "mean_srcport", "median_srcport", "sd_srcport",
               "var_srcport", "mad_srcport", "max_srcport", "min_srcport"]

    out_file.writerow(columns)

    for key in dfs:

        df = dfs[key]

        if (key == "probe.csv"):
            tcp_flows = df[(df["Proto"] == 6) & (df["SrcIP"] == "146.164.69.175")][["SrcIP", "SrcPort"]]
            udp_flows = df[(df["Proto"] == 17) & (df["SrcIP"] == "146.164.69.175")][["SrcIP", "SrcPort"]]
        elif (key == "syn-flood.csv"):
            tcp_flows = df[(df["Proto"] == 6) & (df["SrcIP"] == "228.226.152.83")][["SrcIP", "SrcPort"]]
            udp_flows = df[(df["Proto"] == 17) & (df["SrcIP"] == "228.226.152.83")][["SrcIP", "SrcPort"]]
        elif (key == "land.csv"):
            tcp_flows = df[(df["Proto"] == 6) & (df["SrcIP"] == "10.10.10.3")][["SrcIP", "SrcPort"]]
            udp_flows = df[(df["Proto"] == 17) & (df["SrcIP"] == "10.10.10.3")][["SrcIP", "SrcPort"]]
        else:
            tcp_flows = df[(df["Proto"] == 6) & (df["SrcIP"] == "10.10.10.2")][["SrcIP", "SrcPort"]]
            udp_flows = df[(df["Proto"] == 17) & (df["SrcIP"] == "10.10.10.2")][["SrcIP", "SrcPort"]]

        total_tcp_flows = tcp_flows.shape[0]
        total_udp_flows = udp_flows.shape[0]

        if total_tcp_flows > 0:
            print("# " + str(datetime.datetime.now()) + " - Calculating TCP Wildcard Rules: " + key)
            tcp_mean_srcport = tcp_flows["SrcPort"].mean()
            tcp_median_srcport = tcp_flows["SrcPort"].median()
            tcp_sd_srcport = tcp_flows["SrcPort"].std()
            tcp_var_srcport = tcp_flows["SrcPort"].var()
            tcp_mad_srcport = tcp_flows["SrcPort"].mad()
            tcp_max_srcport = tcp_flows["SrcPort"].max()
            tcp_min_srcport = tcp_flows["SrcPort"].min()
            data = [key, "tcp", total_tcp_flows, tcp_mean_srcport, tcp_median_srcport, tcp_sd_srcport, tcp_var_srcport,
                    tcp_mad_srcport, tcp_max_srcport, tcp_min_srcport]
            out_file.writerow(data)

            plt.figure(figsize=(24, 18))
            plt.title('TCP SrcPort Distribution')
            plt.xlabel('Source Ports')
            plt.ylabel('Frequency')
            plt.hist(tcp_flows["SrcPort"], bins=range(0, 65535, 10))
            plt.legend(loc='upper right')
            plt.savefig(path+"/hist-"+key+"-tcp-srcip.png")

            print("# " + str(datetime.datetime.now()) + " - TCP Wildcard Rules Generated: " + key)

        if total_udp_flows > 0:
            print("# " + str(datetime.datetime.now()) + " - Calculating UDP Wildcard Rules: " + key)
            udp_mean_srcport = udp_flows["SrcPort"].mean()
            udp_median_srcport = udp_flows["SrcPort"].median()
            udp_sd_srcport = udp_flows["SrcPort"].std()
            udp_var_srcport = udp_flows["SrcPort"].var()
            udp_mad_srcport = udp_flows["SrcPort"].mad()
            udp_max_srcport = udp_flows["SrcPort"].max()
            udp_min_srcport = udp_flows["SrcPort"].min()
            data = [key, "udp", total_udp_flows, udp_mean_srcport,
                    udp_median_srcport, udp_sd_srcport, udp_var_srcport, udp_mad_srcport, udp_max_srcport,
                    udp_min_srcport]
            out_file.writerow(data)

            plt.figure(figsize=(24, 18))
            plt.title('UDP SrcPort Distribution')
            plt.xlabel('Source Ports')
            plt.ylabel('Frequency')
            plt.hist(udp_flows["SrcPort"], bins=range(0, 65535, 10))
            plt.legend(loc='upper right')
            plt.savefig(path + "/hist-" + key + "-udp-srcip.png")

            print("# " + str(datetime.datetime.now()) + " - UDP Wildcard Rules Generated: " + key)


    print("### " + str(datetime.datetime.now()) + " - Stats Generated...")

dfs = read_csv_files()
#dfs = generate_full_df(dfs)
#generate_eda(dfs)
generate_stats_wildcards(dfs)