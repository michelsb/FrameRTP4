#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, os, csv

from definitions import DATASET_DIR, array_bound, flow_id, array_time_window, array_pkts_to_start
from util import calculate_metrics, calculate_metrics_bot, create_directory, delete_directory

file_indexes = [0,1,2,4,5,6,7,8,10,12]

def create_directories():
    delete_directory("./stats_bots")
    create_directory("./stats_bots")

def generate_stats():

    create_directories()

    out_file_bot = csv.writer(
        open("./stats_bots/stats.csv", "wb"),
        delimiter=';', quoting=csv.QUOTE_ALL)
    #columns = ["".join(time_windows) for time_windows in array_time_window]
    columns = [0] + array_time_window
    out_file_bot.writerow(columns)

    for index in file_indexes:
        array_line = [index+1]
        for time_window in array_time_window:
            path_file = "./results/scenario-"+str(index)+"/bot_stats_f"+str(index)+"_w"+str(time_window)+".csv"
            f = open(path_file, 'rb')  # opens the csv file
            try:
                reader = csv.reader(f, delimiter=';')  # creates the reader object
                next(reader)
                for row in reader:  # iterates the rows of the file in orders
                    value = float(row[5][1:-1])*100
                array_line.append(value)
            finally:
                f.close()
        out_file_bot.writerow(array_line)

generate_stats()