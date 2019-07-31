#!/usr/bin/env python

import argparse
import grpc
import os
import sys
import commands
import time

from p4thrift_lib.convert import convert_bin_to_ip

from p4switch_lib.p4switch import P4Switch
import p4runtime_lib.helper

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

cms_rows = ["cm_sketch_row1","cm_sketch_row2","cm_sketch_row3","cm_sketch_row4","cm_sketch_row5","global_ctr_packets"]
bf_names = ["bf_flow_filter"]
iblt_ctr_flows = {"ctr_flows":"iblt_ctr_flows"}
iblt_xor_hashes = {"hash1":"iblt_flow_xor_idx1","hash2":"iblt_flow_xor_idx2","hash3":"iblt_flow_xor_idx3"}
iblt_xor_flow_ids = {"proto":"iblt_flow_xor_proto","srcAddr":"iblt_flow_xor_srcAddr","dstAddr":"iblt_flow_xor_dstAddr",
                  "srcPort":"iblt_flow_xor_srcPort","dstPort":"iblt_flow_xor_dstPort","spi":"iblt_flow_xor_spi",
                  "si":"iblt_flow_xor_si"}
iblt_features = {"ctr_packets":"iblt_ctr_packets","first_seen":"iblt_first_seen"}

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

class RTP4ServerController():

    def __init__(self,p4info_file_path,bmv2_file_path):
        self.hostname = commands.getoutput("hostname")  # Get the hostname
        self.p4info_file_path = p4info_file_path
        self.bmv2_file_path = bmv2_file_path
        # Instantiate a P4Runtime helper from the p4info file
        self.p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
        self.switches = []
        self.create_switches()

    def create_switches(self):
        self.switches.append(P4Switch(
            name='s1',
            address='127.0.0.1',
            grpc_port=50051,
            thrift_port=9090,
            device_id=0,
            p4_json_filepath=self.bmv2_file_path,
            proto_dump_file='logs/s1-p4runtime-requests.txt'))
        # self.switches.append(P4Switch(
        #     name='s2',
        #     address='127.0.0.1',
        #     grpc_port=50052,
        #     thrift_port=9091,
        #     device_id=1,
        #     p4_json_filepath=self.bmv2_file_path,
        #     proto_dump_file='logs/s2-p4runtime-requests.txt'))
        # self.switches.append(P4Switch(
        #     name='s3',
        #     address='127.0.0.1',
        #     grpc_port=50053,
        #     thrift_port=9092,
        #     device_id=2,
        #     p4_json_filepath=self.bmv2_file_path,
        #     proto_dump_file='logs/s3-p4runtime-requests.txt'))

    def connect_switches_p4runtime(self):
        for sw in self.switches:
            sw.connect_p4runtime()

    def disconnect_switches_p4runtime(self):
        for sw in self.switches:
            sw.disconnect_p4runtime()

    def connect_switches_p4thrift(self):
        for sw in self.switches:
            sw.connect_p4thrift()

    def disconnect_switches_p4thrift(self):
        for sw in self.switches:
            sw.disconnect_p4thrift()

    # Create XMLRPCLIB Server
    def create_server(self):
        self.server = SimpleXMLRPCServer((self.hostname, 8000),
                                         requestHandler=RequestHandler)
        self.server.register_introspection_functions()
        print "Controller server %s is UP!" % self.hostname

    ####### TABLE

    def writeTableRulePerSwitch(self, sw, table_name, rule):
        table_entry = self.p4info_helper.buildTableEntry(
            table_name=table_name,
            match_fields=rule["match_fields"],
            action_name=rule["action_name"],
            action_params=rule["action_params"],
            priority=rule["priority"])
        sw.WriteTableEntry(table_entry)
        print "Installed rule on %s" % sw.name

    def writeTableRuleAllSwitches(self, table_name, rule):
        response = False
        try:
            self.connect_switches_p4runtime()
            for sw in self.switches:
                self.writeTableRulePerSwitch(sw, table_name, rule)
            response = True
        except KeyboardInterrupt:
            print " Shutting down..."
        except grpc.RpcError as e:
            print(e)
            self.printGrpcError(e)
        self.disconnect_switches_p4runtime()
        return response

    def readTableRulesPerSwitch(self, sw, table_id=None):
        switch_rules = {"sw_name": sw.name, "tables":{}}

        print '\n----- Reading tables rules for %s -----' % sw.name
        for response in sw.ReadTableEntries(table_id=table_id):
            for entity in response.entities:
                entry = entity.table_entry
                # TODO For extra credit, you can use the p4info_helper to translate
                #      the IDs in the entry to names
                table_name = self.p4info_helper.get_tables_name(entry.table_id)
                if table_name not in switch_rules["tables"]:
                    switch_rules["tables"][table_name] = {"id": entry.table_id, "rules":[]}

                rule_entry = {"match_fields":{}}
                for m in entry.match:
                    rule_entry["match_fields"][
                        str(self.p4info_helper.get_match_field_name(table_name, m.field_id))] = str(self.p4info_helper.get_match_field_value(m))

                action = entry.action.action
                action_name = self.p4info_helper.get_actions_name(action.action_id)

                rule_entry["action_name"] = action_name
                rule_entry["action_params"] = {}

                for p in action.params:
                    rule_entry["action_params"][
                        str(self.p4info_helper.get_action_param_name(action_name, p.param_id))] = str(p.value)

                rule_entry["priority"] = entry.priority

                switch_rules["tables"][table_name]["rules"].append(rule_entry)

        return switch_rules

    def readTableRulesAllSwitches(self,table_name):
        response = []
        table_id = self.p4info_helper.get_tables_id(table_name)
        try:
            self.connect_switches_p4runtime()
            for sw in self.switches:
                response.append(self.readTableRulesPerSwitch(sw,table_id=table_id))
        except KeyboardInterrupt:
            print " Shutting down."
        except grpc.RpcError as e:
            self.printGrpcError(e)
        self.disconnect_switches_p4runtime()
        return response

    def deleteTableRulesPerSwitch(self, sw, table_name, rule):
        table_entry = self.p4info_helper.buildTableEntry(
            table_name=table_name,
            match_fields=rule["match_fields"],
            action_name=rule["action_name"],
            action_params=rule["action_params"],
            priority=rule["priority"])
        print(table_entry)
        sw.DeleteTableEntry(table_entry)
        print "Removed rule on %s" % sw.name

    def deleteTableRuleAllSwitches(self,table_name,rule):
        response = False
        #table_id =  self.p4info_helper.get_tables_id(table_name)
        try:
            self.connect_switches_p4runtime()
            for sw in self.switches:
                self.deleteTableRulesPerSwitch(sw,table_name,rule)
            response = True
        except KeyboardInterrupt:
            print " Shutting down."
        except grpc.RpcError as e:
            self.printGrpcError(e)
        self.disconnect_switches_p4runtime()
        return response

    # TESTBED SFC
    def writeSFCClassifierTableRule(self, sw, src_ip_addr, spi, si):
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.sfc_classifier",
            match_fields={
                "hdr.ipv4.srcAddr": (src_ip_addr, 32)
            },
            action_name="MyIngress.sfc_encapsulate",
            action_params={
                "spi": spi,
                "si": si
            })
        sw.WriteTableEntry(table_entry)
        print "Installed ingress tunnel rule on %s" % sw.name

    # TESTBED SFC
    def writeSFFForwardTableRule(self, sw, spi, si, dst_id, is_sff):
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.sfc_sf_forwarder",
            match_fields={
                "hdr.nsh_sp.spi": spi,
                "hdr.nsh_sp.si": si
            },
            action_name="MyIngress.sfc_forward",
            action_params={
                "dst_id": dst_id,
                "is_sff": is_sff
            })
        sw.WriteTableEntry(table_entry)
        print "Installed ingress tunnel rule on %s" % sw.name

    # TESTBED SFC
    def writeSFFDesencapsulateTableRule(self, sw, spi, si):
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.sfc_sf_forwarder",
            match_fields={
                    "hdr.nsh_sp.spi": spi,
                    "hdr.nsh_sp.si": si
            },
            action_name="MyIngress.sfc_desencapsulate",
            action_params={
            })
        sw.WriteTableEntry(table_entry)
        print "Installed ingress tunnel rule on %s" % sw.name

    # TESTBED SFC
    def writeNSHTunnelTableRule(self, sw, dst_id, dst_eth_addr, egress_port):
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.nsh_tunnel_exact",
            match_fields={
                "hdr.nsh_tunnel.dst_id": dst_id
            },
            action_name="MyIngress.nsh_tunnel_forward",
            action_params={
                "dstAddr": dst_eth_addr,
                "port": egress_port
            })
        sw.WriteTableEntry(table_entry)
        print "Installed ingress tunnel rule on %s" % sw.name

    # TESTBED SFC
    def createdSFCRulesOnSwitches(self):
        # Write the SFC rules for s1
        self.writeSFCClassifierTableRule(self.switches[0], "10.0.1.1", 1, 255)
        self.writeSFFDesencapsulateTableRule(self.switches[0], 2, 255)
        self.writeSFCClassifierTableRule(self.switches[0], "10.0.1.2", 2, 255)
        self.writeSFFDesencapsulateTableRule(self.switches[0], 1, 255)


    # TESTBED
    def writeIPV4LPMTableRule(self, sw, dst_ip_addr, dst_eth_addr, egress_port):
        table_entry = self.p4info_helper.buildTableEntry(
            table_name="MyIngress.ipv4_lpm",
            match_fields={
                "hdr.ipv4.dstAddr": (dst_ip_addr, 32)
            },
            action_name="MyIngress.ipv4_forward",
            action_params={
                "dstAddr": dst_eth_addr,
                "port": egress_port
            })
        sw.WriteTableEntry(table_entry)
        print "Installed ingress tunnel rule on %s" % sw.name

    # TESTBED
    def createdForwardingRulesOnSwitches(self):
        # Write the forwarding rules for s1
        self.writeIPV4LPMTableRule(self.switches[0], "10.0.1.1", "00:00:00:00:01:01", 1)
        # Write the forwarding rules for s2
        self.writeIPV4LPMTableRule(self.switches[0], "10.0.1.2", "00:00:00:00:01:02", 2)

    ####### COUNTER

    def readCounterPerSwitch(self, sw, counter_id, index):
        counters = []
        for response in sw.ReadCounters(counter_id, index):
            print(response)
            for entity in response.entities:
                counter = entity.counter_entry
                counters.append(sw.name + " " + counter_id + ": " + str(counter.data.packet_count) + " packets (" + str(counter.data.byte_count) + " bytes)")
        return counters

    def readCounterAllSwitches(self, counter_name, index):
        response = []
        if index is not None:
            counter_id = self.p4info_helper.get_counters_id(counter_name)
            try:
                self.connect_switches_p4runtime()
                for sw in self.switches:
                    response.extend(self.readCounterPerSwitch(sw, counter_id, index))
            except KeyboardInterrupt:
                print " Shutting down."
            except grpc.RpcError as e:
                self.printGrpcError(e)
            self.disconnect_switches_p4runtime()
            return response

    ####### RTP4MON

    def readSFCMonPerSwitch(self, sw):
        response = {}
        for key in iblt_ctr_flows:
            response[key] = sw.ReadRegister(iblt_ctr_flows[key])
        for key in iblt_xor_hashes:
            response[key] = sw.ReadRegister(iblt_xor_hashes[key])
        for key in iblt_xor_flow_ids:
            response[key] = sw.ReadRegister(iblt_xor_flow_ids[key])
        for key in iblt_features:
            if key is "ctr_packets":
                response[key] = sw.ReadCounter(iblt_features[key])
            else:
                response[key] = sw.ReadRegister(iblt_features[key])
        response["timestamp"] = time.time()
        return response

    def readSFCMonAllSwitches(self):
        response = {}
        try:
            self.connect_switches_p4thrift()
            for sw in self.switches:
                response[sw.name] = self.readSFCMonPerSwitch(sw)
        except KeyboardInterrupt:
            print " Shutting down."
        except grpc.RpcError as e:
            self.printGrpcError(e)
        self.disconnect_switches_p4thrift()
        return response

    def resetSFCMonPerSwitch(self, sw):
        #Reset CMS
        for key in cms_rows:
            sw.ResetRegister(key)
        #Reset BF
        for key in bf_names:
            sw.ResetRegister(key)
        #Reset IBLT
        for key in iblt_ctr_flows:
            sw.ResetRegister(iblt_ctr_flows[key])
        for key in iblt_xor_hashes:
            sw.ResetRegister(iblt_xor_hashes[key])
        for key in iblt_xor_flow_ids:
            sw.ResetRegister(iblt_xor_flow_ids[key])
        for key in iblt_features:
            if key is "ctr_packets":
                sw.ResetCounter(iblt_features[key])
            else:
                sw.ResetRegister(iblt_features[key])

    def resetSFCMonAllSwitches(self):
        response = False
        try:
            self.connect_switches_p4thrift()
            for sw in self.switches:
                self.resetSFCMonPerSwitch(sw)
            response = True
        except KeyboardInterrupt:
            print " Shutting down."
        except grpc.RpcError as e:
            self.printGrpcError(e)
        self.disconnect_switches_p4thrift()
        return response

    ####### CREATE SERVICE

    def createRTP4ServiceOnSwitches(self):
        try:
            # Install the P4 program on the switches
            self.switches[0].SetForwardingPipelineConfig(p4info=self.p4info_helper.p4info,bmv2_json_file_path=self.bmv2_file_path)
            print "Installed P4 Program ("+self.bmv2_file_path+") using SetForwardingPipelineConfig on s1"
            # self.switches[1].SetForwardingPipelineConfig(p4info=self.p4info_helper.p4info,bmv2_json_file_path=self.bmv2_file_path)
            # print "Installed RT P4 Program using SetForwardingPipelineConfig on s2"
            # self.switches[2].SetForwardingPipelineConfig(p4info=self.p4info_helper.p4info,bmv2_json_file_path=self.bmv2_file_path)
            # print "Installed RT P4 Program using SetForwardingPipelineConfig on s3"
        except KeyboardInterrupt:
         print " Shutting down."
        except grpc.RpcError as e:
         self.printGrpcError(e)

    def printGrpcError(self,e):
        print "gRPC Error:", e.details(),
        status_code = e.code()
        print "(%s)" % status_code.name,
        traceback = sys.exc_info()[2]
        print "[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno)

    def createRTP4Service(self):
        try:
            self.connect_switches_p4runtime()
            self.createRTP4ServiceOnSwitches()
            # TEST
            self.createdForwardingRulesOnSwitches()
            # TEST SFC
            self.createdSFCRulesOnSwitches()
        except KeyboardInterrupt:
            print " Shutting down."
        except grpc.RpcError as e:
            self.printGrpcError(e)
        self.disconnect_switches_p4runtime()

    def startAgentService(self):
        self.create_server()
        self.createRTP4Service()
        self.server.register_function(self.writeTableRuleAllSwitches, 'write_rule')
        self.server.register_function(self.readTableRulesAllSwitches, 'read_rules')
        self.server.register_function(self.deleteTableRuleAllSwitches, 'delete_rule')
        self.server.register_function(self.readSFCMonAllSwitches, 'read_sfcmon')
        self.server.register_function(self.resetSFCMonAllSwitches, 'reset_sfcmon')
        #self.server.register_function(self.readCounterAllSwitches, 'read_counters')
        self.server.serve_forever()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='./build/rtp4app.p4info')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='./build/rtp4app.json')
    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print "\np4info file not found: %s\nHave you run 'make'?" % args.p4info
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print "\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json
        parser.exit(1)
    # Run the server's main loop
    try:
        print 'Use Control-C to exit'
        agent = RTP4ServerController(args.p4info, args.bmv2_json)
        #print agent.get_stats()
        agent.startAgentService()
    except KeyboardInterrupt:
        print 'Exiting'
    #main(args.p4info, args.bmv2_json)
