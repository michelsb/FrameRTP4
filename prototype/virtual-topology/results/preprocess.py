#!/usr/bin/env python2
#  -*- coding: utf-8 -*-

import csv     # imports the csv module
import sys, subprocess
from shutil import copyfile

reload(sys)  
sys.setdefaultencoding('utf8')

array_scenario = ["sfc_sfcmon","sfc_p4tables","sfc_without_mon"]
#array_packet_size = [64,128,256,512,1024,1280]
#array_num_flows = [10000,20000,30000,40000,50000]
#default_num_flows = 10000
#rounds = 31

array_packet_size = [512]
array_num_flows = [1,10000,20000,30000,40000]
default_num_flows = 40000
rounds = 30


for scenario in array_scenario:

	subprocess.Popen("rm -rf ./consolidated/"+scenario, shell=True).wait()
	subprocess.Popen("mkdir -p ./consolidated/"+scenario, shell=True).wait()

	for num_flows in array_num_flows:
		if (scenario == "sfc_p4tables") or (num_flows == default_num_flows):
			try:
				source = "./raw/"+scenario+"/iperf-"+scenario+"-"+str(num_flows)+".txt"
				target = "./consolidated/"+scenario+"/iperf-"+scenario+"-"+str(num_flows)+".log"
				copyfile(source, target)
			except IOError as e:
				print("Unable to copy file. %s" % e)
				sys.exit(1)
			except:
				print("Unexpected error:", sys.exc_info())
				sys.exit(1)
			for packet_size in array_packet_size:
				new_file = open("./consolidated/"+scenario+"/ditg-"+scenario+"-"+str(packet_size)+"-"+str(num_flows)+".log", 'wb')
				new_file_writer = csv.writer(new_file, delimiter=' ', quoting=csv.QUOTE_MINIMAL)
				
				for round in range(2,rounds+1):
					row = []
					with open("./raw/"+scenario+"/summary-"+scenario+"-"+str(packet_size)+"-"+str(num_flows)+"-"+str(round)+".txt") as f:
						for line in f:    	
							elements = line.split()
							if len(elements) >= 4:
								if elements[0] != '****************':
									if elements[1] == 'packets' or elements[0] == 'Minimum' or elements[0] == 'Maximum' or (elements[0] == 'Average' and (elements[1] == 'delay' or elements[1] == 'jitter' or elements[1] == 'bitrate')):
										row.append(float(elements[3]))
									if elements[2] == 'rate':
										row.append(float(elements[4]))
									if elements[1] == 'dropped':
										row.append(float(elements[4][1:]))    			
								else:
									break
					new_file_writer.writerow(row)			
				new_file.close()

