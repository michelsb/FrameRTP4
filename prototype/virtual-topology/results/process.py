#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv     # imports the csv module
import rpy2.robjects as robjects
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sys 
import os 

reload(sys)
sys.setdefaultencoding('utf8')


array_scenario = {"sfc_without_mon":"No Monitoring", "sfc_sfcmon":"SFCMon", "sfc_p4tables":"P4 Table"}

#array_scenario_order = ["sfc_without_mon", "sfc_sfcmon", "sfc_p4tables"]
array_scenario_order = ["sfc_sfcmon", "sfc_p4tables"]
array_scenario_color = {"sfc_without_mon":"m", "sfc_sfcmon":"c", "sfc_p4tables":"r"}
# array_packet_size = [64,128,256,512,1024,1280]
# array_num_flows = [10000,20000,30000,40000,50000]
# default_num_flows = 10000
# rounds = 31

array_packet_size = [512]
#array_num_flows = [1,10000,20000,30000,40000]
array_num_flows = [1,20000,40000]
default_num_flows = 40000
rounds = 30

# 0 - Total Packets
# 1 - Minimum delay (s)
# 2 - Maximum delay (s)
# 3 - Average delay (s)
# 4 - Average jitter (s)
# 5 - Average packet rate (kbps)
# 6 - Average bitrate (pps)
# 7 - Packets dropped rate (%)

#metrics = ["bandwidth-mbps","latency","jitter","packet-loss"]
metrics = ["bandwidth-mbps","latency","jitter"]
factors = ["packet_size","num_flows"]
metrics_position = {"bandwidth-mbps":5,"latency":3,"jitter":4,"packet-loss":7}
metrics_title = {"bandwidth-mbps":"Throughput (Mbps)","latency":"Latency (Milliseconds)","jitter":"Jitter (Milliseconds)","packet-loss":"Packet Loss Rate (%)"}
factors_title = {"packet_size":"Frame Size (Bytes)","num_flows":"Number of Flows"} 
metric_iperf = metrics[0]

confidence_interval = 0.05

os.system("rm -rf ./figures ./norm-tests ./np-tests")

for factor in factors:
	os.system("mkdir -p ./np-tests/"+factor)

for scenario in array_scenario:
	for metric in metrics:
		os.system("mkdir -p ./figures/eda/ditg-"+scenario+"/"+metric)		
		os.system("mkdir -p ./norm-tests/ditg-"+scenario+"/"+metric)
		os.system("mkdir -p ./figures/eda/iperf-"+scenario+"/"+metric)		
		os.system("mkdir -p ./norm-tests/iperf-"+scenario+"/"+metric)

for metric in metrics:
	for factor in factors:
		os.system("mkdir -p ./figures/"+factor+"/"+metric)
		

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

result_norm_test_iperf = open('./norm-tests/result-norm-test-iperf.csv', 'wb') # opens the csv file
result_norm_test_iperf_writer = csv.writer(result_norm_test_iperf, delimiter=' ', quoting=csv.QUOTE_MINIMAL)	
result_norm_test_iperf_writer.writerow(['Scenario','Num Flows','Metric', 'P-Value'])

result_norm_test_ditg = open('./norm-tests/result-norm-test-ditg.csv', 'wb') # opens the csv file
result_norm_test_ditg_writer = csv.writer(result_norm_test_ditg, delimiter=' ', quoting=csv.QUOTE_MINIMAL)	
result_norm_test_ditg_writer.writerow(['Scenario','Num Flows', 'Packet Size', 'Metric', 'P-Value'])

vector_samples_ditg = {}
vector_samples_iperf = {}

for scenario in array_scenario:	

	title = array_scenario[scenario]

	vector_samples_ditg[scenario] = {}
	vector_samples_iperf[scenario] = {}

	for num_flows in array_num_flows:
		
		if (scenario == "sfc_p4tables") or (num_flows == default_num_flows):
			num_flows = str(num_flows)
			vector_samples_ditg[scenario][num_flows] = dict()
			vector_samples_iperf[scenario][num_flows] = {metric_iperf:{}}
			
			# STARTING IPERF RESULTS PROCESSING
			
			f = open("./consolidated/"+scenario+"/iperf-"+scenario+"-"+num_flows+".log", 'rb') # opens the csv file

			try:
				array_rates = []
				reader = csv.reader(f,delimiter=' ') #creates the reader object
				for row in reader:   # iterates the rows of the file in orders		    	
					tester = False
					value = float(row[0])
					if value < 0.0:
						tester = True
					if tester:
						print("Found negative values! Stopping...")
						sys.exit(1)
					array_rates.append(value)					
			finally:
					f.close()  

			# EDA IPERF

			title_graph = title +" - "+num_flows+" Flow(s)"

			vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"] = robjects.FloatVector(array_rates)
			vector_samples_iperf[scenario][num_flows][metric_iperf]["median"] = r.median(vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"])[0]
			vector_samples_iperf[scenario][num_flows][metric_iperf]["mean"] = r.mean(vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"])
			vector_samples_iperf[scenario][num_flows][metric_iperf]["sd"] = r.sd(vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"])
			vector_samples_iperf[scenario][num_flows][metric_iperf]["max"] = r.max(vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"])[0]
			vector_samples_iperf[scenario][num_flows][metric_iperf]["min"] = r.min(vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"])[0]
			
			if vector_samples_iperf[scenario][num_flows][metric_iperf]["median"] != 0:
			
				xlabel = metrics_title[metric_iperf]

				# Histograma
				r.pdf("./figures/eda/iperf-"+scenario+"/"+metric_iperf+"/hist-"+metric_iperf+"-"+scenario+"-"+num_flows+".pdf")
				r.hist(vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"], main = title_graph, col="blue", xlab = xlabel, ylab = "Frequência Absoluta")
				close_pdf()
				# Boxplots
				r.pdf("./figures/eda/iperf-"+scenario+"/"+metric_iperf+"/box-"+metric_iperf+"-"+scenario+"-"+num_flows+".pdf")
				r.boxplot(vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"], main = title_graph,col="lightblue", horizontal=True, las=1, xlab=xlabel)
				close_pdf()
				# Grafico de probabilidade (QQ)
				r.pdf("./figures/eda/iperf-"+scenario+"/"+metric_iperf+"/qq-"+metric_iperf+"-"+scenario+"-"+num_flows+".pdf")
				r.qqnorm(vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"], main = title_graph, xlab = "Quantis teóricos N(0,1)", pch = 20, ylab = xlabel)
				r.qqline(vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"], lty = 2, col = "red")
				close_pdf()

				filename_norm_tests_iperf = "./norm-tests/iperf-"+scenario+"/"+metric_iperf+"/norm-tests-"+metric_iperf+"-"+scenario+"-"+num_flows+".csv"
				norm_tests_iperf = open(filename_norm_tests_iperf, 'wb') # opens the csv file		
				tester = False			

				try:			
					norm_tests_iperf_writer = csv.writer(norm_tests_iperf, delimiter=' ', quoting=csv.QUOTE_MINIMAL)			
					norm_tests_iperf_writer.writerow(['Method', 'Statistic', 'P-Value','Alternative Hypothesis (KS Test)'])		 
								
					test = lillie(vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"])
					norm_tests_iperf_writer.writerow([test[2][0], test[0][0],test[1][0],''])		 	 		
					if (float(test[1][0]) >= confidence_interval):
						tester=True
					p_value = "{:.2e}".format(test[1][0])
					if tester: 
							result_norm_test_iperf_writer.writerow([scenario,num_flows,metric,p_value])
				finally:
					norm_tests_iperf.close()
							
				test_wilcoxon = wilcoxon_test_one_sample(vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"])							
				error_max = test_wilcoxon[7][1]		
				median = test_wilcoxon[8][0]

				vector_samples_iperf[scenario][num_flows][metric_iperf]["wilcoxon_test_median"] = median
				vector_samples_iperf[scenario][num_flows][metric_iperf]["wilcoxon_test_error"] = float(error_max)-float(median)			

				t_test = t_test_one_sample(vector_samples_iperf[scenario][num_flows][metric_iperf]["sample"])
				error_max = t_test[3][1]
				mean = t_test[5][0]

				vector_samples_iperf[scenario][num_flows][metric_iperf]["t_test_mean"] = mean
				vector_samples_iperf[scenario][num_flows][metric_iperf]["t_test_error"] = float(
					error_max) - float(mean)

			# STARTING DITG RESULTS PROCESSING			
			
			for packet_size in array_packet_size:
				packet_size = str(packet_size)
				vector_samples_ditg[scenario][num_flows][packet_size] = dict()

				f = open("./consolidated/"+scenario+"/ditg-"+scenario+"-"+packet_size+"-"+num_flows+".log", 'rb') # opens the csv file

				try:
					array_metric = dict()
					for metric in metrics:
							vector_samples_ditg[scenario][num_flows][packet_size][metric]=dict()
							array_metric[metric]=[]
					reader = csv.reader(f,delimiter=' ') #creates the reader object
					for row in reader:   # iterates the rows of the file in orders		    	
						tester = False
						for metric in metrics:
							value = float(row[metrics_position[metric]])
							if value < 0.0:
								tester = True
						if tester:
							print("Found negative values! Stopping...")
							break
						for metric in metrics:		 	        	
							value = float(row[metrics_position[metric]])
							if metric == "latency" or metric == "jitter":
								array_metric[metric].append(value*1000)
							elif metric == "bandwidth-mbps":
								array_metric[metric].append(value/1000)
							else: 
								array_metric[metric].append(value)
				finally:
					f.close()  

				# EDA DITG
				
 				title_graph = title + " - Packet Size (bytes): " + packet_size + " - "+num_flows+" Flow(s)"

				for metric in metrics:
				
					vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"] = robjects.FloatVector(array_metric[metric])
					vector_samples_ditg[scenario][num_flows][packet_size][metric]["median"] = r.median(vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"])[0]
					vector_samples_ditg[scenario][num_flows][packet_size][metric]["mean"] = r.mean(vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"])
					vector_samples_ditg[scenario][num_flows][packet_size][metric]["sd"] = r.sd(vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"])
					vector_samples_ditg[scenario][num_flows][packet_size][metric]["max"] = r.max(vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"])[0]
					vector_samples_ditg[scenario][num_flows][packet_size][metric]["min"] = r.min(vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"])[0]

					if vector_samples_ditg[scenario][num_flows][packet_size][metric]["median"] != 0:

						xlabel = metrics_title[metric]

						# Histograma
						r.pdf("./figures/eda/ditg-"+scenario+"/"+metric+"/hist-"+metric+"-"+scenario+"-"+packet_size+"-"+num_flows+".pdf")
						r.hist(vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"], main = title_graph, col="blue", xlab = xlabel, ylab = "Frequência Absoluta")
						close_pdf()
						# Boxplots
						r.pdf("./figures/eda/ditg-"+scenario+"/"+metric+"/box-"+metric+"-"+scenario+"-"+packet_size+"-"+num_flows+".pdf")
						r.boxplot(vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"], main = title_graph,col="lightblue", horizontal=True, las=1, xlab=xlabel)
						close_pdf()
						# Grafico de probabilidade (QQ)
						r.pdf("./figures/eda/ditg-"+scenario+"/"+metric+"/qq-"+metric+"-"+scenario+"-"+packet_size+"-"+num_flows+".pdf")
						r.qqnorm(vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"], main = title_graph, xlab = "Quantis teóricos N(0,1)", pch = 20,
						ylab = xlabel)
						r.qqline(vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"], lty = 2, col = "red")
						close_pdf()

						filename_norm_tests_ditg = "./norm-tests/ditg-"+scenario+"/"+metric+"/norm-tests-"+metric+"-"+scenario+"-"+packet_size+"-"+num_flows+".csv"
						norm_tests_ditg = open(filename_norm_tests_ditg, 'wb') # opens the csv file		
							
						tester = False
						#methods= ""
						#p_values= ""
						#count=0

						try:			
							norm_tests_ditg_writer = csv.writer(norm_tests_ditg, delimiter=' ', quoting=csv.QUOTE_MINIMAL)			
							norm_tests_ditg_writer.writerow(['Method', 'Statistic', 'P-Value','Alternative Hypothesis (KS Test)'])		 
							
							test = lillie(vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"])
							norm_tests_ditg_writer.writerow([test[2][0], test[0][0],test[1][0],''])		 	 		
							if (float(test[1][0]) >= confidence_interval):
								tester=True										 	 		
							
							p_value = "{:.2e}".format(test[1][0])

							if tester: 
								result_norm_test_ditg_writer.writerow([scenario,num_flows,packet_size,metric,p_value])

						finally:
							norm_tests_ditg.close()		 	 			
						
						test_wilcoxon = wilcoxon_test_one_sample(vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"])							
						error_max = test_wilcoxon[7][1]		
						median = test_wilcoxon[8][0]

						vector_samples_ditg[scenario][num_flows][packet_size][metric]["wilcoxon_test_median"] = median
						vector_samples_ditg[scenario][num_flows][packet_size][metric]["wilcoxon_test_error"] = float(error_max)-float(median)

						t_test = t_test_one_sample(vector_samples_ditg[scenario][num_flows][packet_size][metric]["sample"])
						error_max = t_test[3][1]
						mean = t_test[5][0]

						vector_samples_ditg[scenario][num_flows][packet_size][metric]["t_test_mean"] = mean
						vector_samples_ditg[scenario][num_flows][packet_size][metric]["t_test_error"] = float(
							error_max) - float(mean)

result_norm_test_iperf.close()
result_norm_test_ditg.close()

## Creating Charts DITG ##

fig_num = 0
factor_charts = factors[1]
default_packet_size = "512"


width = 0.35  # the width of the bars
opacity = 0.5
error_config = {'ecolor': 'black'}

vectors_median = {}
vectors_errors = {}

x = np.arange(len(array_num_flows))

for metric in metrics:
	ylabel = metrics_title[metric]
	fig_num = fig_num + 1
	plt.figure(fig_num)
	fig, ax = plt.subplots()
	rects = []
	pos = x
	for scenario in array_scenario_order:
		vectors_median[scenario] = []
		vectors_errors[scenario] = []
		for num_flows in array_num_flows:
			if (scenario == "sfc_p4tables"):
				num_flows = str(num_flows)
			else:
				num_flows = str(default_num_flows)
			vectors_median[scenario].append(
				vector_samples_ditg[scenario][num_flows][default_packet_size][metric]["wilcoxon_test_median"])
			vectors_errors[scenario].append(
				vector_samples_ditg[scenario][num_flows][default_packet_size][metric]["wilcoxon_test_error"])
			#vectors_median[scenario].append(vector_samples_ditg[scenario][num_flows][default_packet_size][metric]["t_test_mean"])
			#vectors_errors[scenario].append(vector_samples_ditg[scenario][num_flows][default_packet_size][metric]["t_test_error"])
		rect = ax.bar(pos, vectors_median[scenario], width, alpha=opacity, color=array_scenario_color[scenario], yerr=vectors_errors[scenario],
					  error_kw=error_config)
		rects.append(rect)
		pos = pos + width
	#ax.set_ylabel(ylabel)
	#ax.set_xlabel(factors_title[factor_charts])
	fig.text(0.5, 0.01, factors_title[factor_charts], ha='center', fontsize=16)
	fig.text(0.01, 0.5, ylabel, va='center', rotation='vertical', fontsize=16)
	ax.set_title("")
	ax.set_xticks(x + (width/2))
	ax.set_xticklabels(array_num_flows,fontsize=14)
	ax.tick_params(labelsize=14)
	legend_classes = tuple([rect[0] for rect in rects])
	legend_titles = tuple([array_scenario[scenario] for scenario in array_scenario_order])
	ax.legend(legend_classes, legend_titles, bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=2, mode="expand",
			  borderaxespad=0.,prop={'size':16})
	plt.savefig("./figures/" + factor_charts + "/" + metric + "/ditg-" + metric + "-" + factor_charts + ".pdf",
				format='pdf')

## Creating Charts IPERF ##

ylabel = metrics_title[metric_iperf]
fig_num = fig_num + 1
plt.figure(fig_num)
fig, ax = plt.subplots()
rects = []
pos = x
for scenario in array_scenario_order:
	vectors_median[scenario] = []
	vectors_errors[scenario] = []
	for num_flows in array_num_flows:
		if (scenario == "sfc_p4tables"):
			num_flows = str(num_flows)
		else:
			num_flows = str(default_num_flows)
		vectors_median[scenario].append(vector_samples_iperf[scenario][num_flows][metric_iperf]["wilcoxon_test_median"])
		vectors_errors[scenario].append(vector_samples_iperf[scenario][num_flows][metric_iperf]["wilcoxon_test_error"])
		#vectors_median[scenario].append(vector_samples_iperf[scenario][num_flows][metric_iperf]["t_test_mean"])
		#vectors_errors[scenario].append(vector_samples_iperf[scenario][num_flows][metric_iperf]["t_test_error"])
	rect = ax.bar(pos, vectors_median[scenario], width, alpha=opacity, color=array_scenario_color[scenario], yerr=vectors_errors[scenario],
				  error_kw=error_config)
	rects.append(rect)
	pos = pos + width
#ax.set_ylabel(ylabel)
#ax.set_xlabel(factors_title[factor_charts])
fig.text(0.5, 0.01, factors_title[factor_charts], ha='center', fontsize=16)
fig.text(0.01, 0.5, ylabel, va='center', rotation='vertical', fontsize=16)
ax.set_title("")
ax.set_xticks(x + (width/2))
ax.set_xticklabels(array_num_flows,fontsize=14)
ax.tick_params(labelsize=14)
legend_classes = tuple([rect[0] for rect in rects])
legend_titles = tuple([array_scenario[scenario] for scenario in array_scenario_order])
ax.legend(legend_classes, legend_titles, bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=2, mode="expand",
		  borderaxespad=0.,prop={'size':16})
plt.savefig("./figures/" + factor_charts + "/" + metric_iperf + "/iperf-" + metric_iperf + "-" + factor_charts + ".pdf",
			format='pdf')








## Creating Charts DITG ##

#fig_num=0

## Chart 1 = Latency x Packet Size 
## Chart 2 = Latency x Num Flows
## Chart 3 = Throughput x Num Flows (iperf)


## Charts: Fixed Num Flows

# factor_charts = factors[0]
# vectors_median = {}
# vectors_errors = {}
#
# x = np.arange(len(array_packet_size))
#
# for metric in metrics:
# 	ylabel = metrics_title[metric]
# 	fig_num = fig_num + 1
# 	plt.figure(fig_num)
# 	width = 0.35       # the width of the bars
# 	opacity = 0.5
# 	error_config = {'ecolor': 'black'}
# 	fig, ax = plt.subplots()
# 	rects = []
# 	pos = x
# 	for scenario in array_scenario:
# 		vectors_median[scenario] = []
# 		vectors_errors[scenario] = []
# 		for packet_size in array_packet_size:
# 			vectors_median[scenario].append(vector_samples_ditg[scenario][default_num_flows][packet_size][metric]["wilcoxon_test_median"])
# 			vectors_errors[scenario].append(vector_samples_ditg[scenario][default_num_flows][packet_size][metric]["wilcoxon_test_error"])
# 		rect = ax.bar(pos, vectors_median[scenario], width, alpha=opacity, color='m',yerr=vectors_errors[scenario],error_kw=error_config)
# 		rects.append(rect)
# 		pos = pos + width
# 	ax.set_ylabel(ylabel)
# 	ax.set_xlabel(factors_title[factor_charts])
# 	ax.set_title("")
# 	ax.set_xticks(x + width)
# 	ax.set_xticklabels(array_packet_size)
# 	legend_classes = tuple([rect[0] for rect in rects])
# 	legend_titles = tuple([array_scenario[scenario] for scenario in array_scenario])
# 	ax.legend(legend_classes, legend_titles,bbox_to_anchor=(0., 1.02, 1., .102), loc=3,ncol=2, mode="expand", borderaxespad=0.)
# 	plt.savefig("./figures/"+factor_charts+"/"+metric+"/ditg-"+metric+"-"+factor_charts+".pdf",format='pdf')







