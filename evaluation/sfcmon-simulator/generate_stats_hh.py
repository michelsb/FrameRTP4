#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, os, csv
import numpy as np
import rpy2.robjects as robjects
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from definitions import metrics, metrics_position, metrics_properties, array_bound, array_time_window

reload(sys)
sys.setdefaultencoding('utf8')

r = robjects.r
r.library("nortest")
r.library("MASS")

r('''
        wilcox.onesample.test <- function(v, verbose=FALSE) {
           wilcox.test(v,mu=median(v),conf.int=TRUE, conf.level = 0.95)
        }
        wilcox.twosamples.test <- function(v, r, verbose=FALSE) {
           wilcox.test(v,r)
        }
        tstudent.onesample.test <- function(v, verbose=FALSE) {
           t.test(v, mu = mean(v), alternative = "two.sided")
        }
        ''')

# Normality Test
lillie = robjects.r('lillie.test') # Lilliefors

# Close pdf graphics
close_pdf = robjects.r('dev.off')

# Non-parametric Tes
wilcoxon_test_two_samples = robjects.r['wilcox.twosamples.test']
wilcoxon_test_one_sample = robjects.r['wilcox.onesample.test']
t_test_one_sample = robjects.r['tstudent.onesample.test']

def generate_stats():
    os.system("rm -rf ./figures ")
    os.system("mkdir -p ./figures")

    vectors_metrics = {}
    r_vectors_metrics = {}

    f = open("./results/stats_file_packets.csv", 'rb')  # opens the csv file

    try:
        array_rates = []
        reader = csv.reader(f, delimiter=',')  # creates the reader object
        tester = True
        for row in reader:  # iterates the rows of the file in orders
            if tester:
                tester = False
                continue
            if ''.join(row).strip():
                num_chunks = row[0]
                if row[0] not in vectors_metrics:
                    vectors_metrics[num_chunks] = {}
                    r_vectors_metrics[num_chunks] = {}
                for metric in metrics:
                    if metric not in vectors_metrics[num_chunks]:
                        vectors_metrics[num_chunks][metric] = []
                        r_vectors_metrics[num_chunks][metric] = {}
                    vectors_metrics[num_chunks][metric].append(float(row[metrics_position[metric]]))

    finally:
        f.close()

    vector_medians = {}
    vector_errors = {}

    for metric in metrics:
        if metric not in vector_medians:
            vector_medians[metric] = []
            vector_errors[metric] = []
        for num_chunks in array_num_chunks:
            num_chunks = str(num_chunks)
            if metric == "recall":
                vector_medians[metric].append(100)
                vector_errors[metric].append(0)
            else:
                r_sample = robjects.FloatVector(vectors_metrics[num_chunks][metric])
                r_vectors_metrics[num_chunks][metric]["sample"] = r_sample
                t_test = t_test_one_sample(r_sample)
                error_max = t_test[3][1]
                mean = t_test[5][0]
                r_vectors_metrics[num_chunks][metric]["t_test_mean"] = mean
                r_vectors_metrics[num_chunks][metric]["t_test_error"] = float(error_max) - float(mean)
                vector_medians[metric].append(r_vectors_metrics[num_chunks][metric]["t_test_mean"]*100)
                vector_errors[metric].append(r_vectors_metrics[num_chunks][metric]["t_test_error"]*100)


    fig_num = 0
    x = np.arange(len(array_num_chunks))+1
    ylabel = "Performance Measures (%)"
    plt.figure(fig_num)
    fig, ax = plt.subplots()

    #time_window = [10, 9, 7, 5, 3, 1]

    for metric in metrics:
        ax.errorbar(x, vector_medians[metric],
                    yerr=vector_errors[metric], color=metrics_properties[metric]["color"],
                    marker=metrics_properties[metric]["marker"], mfc=metrics_properties[metric]["color"],
                    mec=metrics_properties[metric]["color"], ms=8, label=metrics_properties[metric]["title"])

    fig.text(0.5, 0.01, "Stream Time Window (seconds)", ha='center', fontsize=16)
    fig.text(0.01, 0.5, ylabel, va='center', rotation='vertical', fontsize=16)

    #ax.set_xticklabels([60/i for i in array_num_chunks], fontsize=14)
    #print x
    ax.set_xticklabels([60/i for i in array_num_chunks], fontsize=14)
    ax.tick_params(labelsize=14)
    ax.set_xticks(x)
    ax.legend(prop={'size': 12})
    plt.savefig("./figures/metrics.pdf", format='pdf')

    plt.close()

generate_stats()