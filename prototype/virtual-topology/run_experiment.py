#!/usr/bin/env python2
import os, sys, json, subprocess, re, argparse
from time import sleep

from p4mininet_lib.p4_mininet import P4Switch, P4Host

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import lg, output

from p4mininet_lib.p4runtime_switch import P4RuntimeSwitch
import p4runtime_lib.simple_controller



#MAIN
#num_rounds = 30
round_time_ditg = 10000
round_time_iperf = 10
#num_flows = [10000, 20000, 30000, 40000, 50000]
#fixed_num_flows = 10000
#packet_size = [64, 128, 256, 512, 1024, 1280]
default_packet_size = 512
rate_bits = 10000000

# TEST
num_rounds = 30
num_flows = [1, 10000, 20000, 30000, 40000]
fixed_num_flows = 40000
packet_size = [512]
#rate_bits = 5000000

first_src_port = 1
first_dst_port = 9001

def configureP4Switch(**switch_args):
    """ Helper class that is called by mininet to initialize
        the virtual P4 switches. The purpose is to ensure each
        switch's thrift server is using a unique port.
    """
    if "sw_path" in switch_args and 'grpc' in switch_args['sw_path']:
        # If grpc appears in the BMv2 switch target, we assume will start P4Runtime
        class ConfiguredP4RuntimeSwitch(P4RuntimeSwitch):
            def __init__(self, *opts, **kwargs):
                kwargs.update(switch_args)
                P4RuntimeSwitch.__init__(self, *opts, **kwargs)

            def describe(self):
                print "%s -> gRPC port: %d" % (self.name, self.grpc_port)

        return ConfiguredP4RuntimeSwitch
    else:
        class ConfiguredP4Switch(P4Switch):
            next_thrift_port = 9090
            def __init__(self, *opts, **kwargs):
                global next_thrift_port
                kwargs.update(switch_args)
                kwargs['thrift_port'] = ConfiguredP4Switch.next_thrift_port
                ConfiguredP4Switch.next_thrift_port += 1
                P4Switch.__init__(self, *opts, **kwargs)

            def describe(self):
                print "%s -> Thrift port: %d" % (self.name, self.thrift_port)

        return ConfiguredP4Switch


class ExperimentTopo(Topo):
    """ The mininet topology class for the P4 tutorial exercises.
        A custom class is used because the exercises make a few topology
        assumptions, mostly about the IP and MAC addresses.
    """
    def __init__(self, hosts, switches, links, log_dir, **opts):
        Topo.__init__(self, **opts)
        host_links = []
        switch_links = []
        self.sw_port_mapping = {}

        for link in links:
            if link['node1'][0] == 'h':
                host_links.append(link)
            else:
                switch_links.append(link)

        link_sort_key = lambda x: x['node1'] + x['node2']
        # Links must be added in a sorted order so bmv2 port numbers are predictable
        host_links.sort(key=link_sort_key)
        switch_links.sort(key=link_sort_key)

        for sw in switches:
            #self.addSwitch(sw, log_file="%s/%s.log" %(log_dir, sw))
            self.addSwitch(sw)

        for link in host_links:
            host_name = link['node1']
            host_sw   = link['node2']
            host_num = int(host_name[1:])
            sw_num   = int(host_sw[1:])
            host_ip = "10.0.%d.%d" % (sw_num, host_num)
            host_mac = '00:00:00:00:%02x:%02x' % (sw_num, host_num)
            # Each host IP should be /24, so all exercise traffic will use the
            # default gateway (the switch) without sending ARP requests.
            self.addHost(host_name, ip=host_ip+'/24', mac=host_mac)
            self.addLink(host_name, host_sw,
                         delay=link['latency'], bw=link['bandwidth'],
                         addr1=host_mac, addr2=host_mac)
            self.addSwitchPort(host_sw, host_name)

        for link in switch_links:
            self.addLink(link['node1'], link['node2'],
                        delay=link['latency'], bw=link['bandwidth'])
            self.addSwitchPort(link['node1'], link['node2'])
            self.addSwitchPort(link['node2'], link['node1'])

        self.printPortMapping()

    def addSwitchPort(self, sw, node2):
        if sw not in self.sw_port_mapping:
            self.sw_port_mapping[sw] = []
        portno = len(self.sw_port_mapping[sw])+1
        self.sw_port_mapping[sw].append((portno, node2))

    def printPortMapping(self):
        print "Switch port mapping:"
        for sw in sorted(self.sw_port_mapping.keys()):
            print "%s: " % sw,
            for portno, node2 in self.sw_port_mapping[sw]:
                print "%d:%s\t" % (portno, node2),
            print


class ExperimentRunner:
    """
        Attributes:
            log_dir  : string   // directory for mininet log files
            pcap_dir : string   // directory for mininet switch pcap files
            quiet    : bool     // determines if we print logger messages

            hosts    : list<string>       // list of mininet host names
            switches : dict<string, dict> // mininet host names and their associated properties
            links    : list<dict>         // list of mininet link properties

            switch_json : string // json of the compiled p4 example
            bmv2_exe    : string // name or path of the p4 switch binary

            topo : Topo object   // The mininet topology instance
            net : Mininet object // The mininet instance

    """
    def logger(self, *items):
        if not self.quiet:
            print(' '.join(items))

    def formatLatency(self, l):
        """ Helper method for parsing link latencies from the topology json. """
        if isinstance(l, (str, unicode)):
            return l
        else:
            return str(l) + "ms"

    def __init__(self, topo_file, log_dir, pcap_dir,
                 switch_json_scenario1, switch_json_scenario2, switch_json_scenario3, bmv2_exe='simple_switch', quiet=False):
        """ Initializes some attributes and reads the topology json. Does not
            actually run the exercise. Use run_exercise() for that.

            Arguments:
                topo_file : string    // A json file which describes the exercise's
                                         mininet topology.
                log_dir  : string     // Path to a directory for storing exercise logs
                pcap_dir : string     // Ditto, but for mininet switch pcap files
                switch_json : string  // Path to a compiled p4 json for bmv2
                bmv2_exe    : string  // Path to the p4 behavioral binary
                quiet : bool          // Enable/disable script debug messages
        """

        self.quiet = quiet
        self.logger('Reading topology file.')
        with open(topo_file, 'r') as f:
            topo = json.load(f)
        self.hosts = topo['hosts']
        self.switches = topo['switches']
        self.links = self.parse_links(topo['links'])

        # Ensure all the needed directories exist and are directories
        for dir_name in [log_dir, pcap_dir]:
            if not os.path.isdir(dir_name):
                if os.path.exists(dir_name):
                    raise Exception("'%s' exists and is not a directory!" % dir_name)
                os.mkdir(dir_name)
        self.log_dir = log_dir
        self.pcap_dir = pcap_dir
        self.switch_json = {}
        self.switch_json["sfc_sfcmon"] = switch_json_scenario1
        self.switch_json["sfc_without_mon"] = switch_json_scenario2
        self.switch_json["sfc_p4tables"] = switch_json_scenario3
        self.bmv2_exe = bmv2_exe

    def waitListening(self, client, server, port):
        "Wait until server is listening on port"
        if not 'telnet' in client.cmd('which telnet'):
            raise Exception('Could not find telnet')
        cmd = ('sh -c "echo A | telnet -e A %s %s"' %
               (server.IP(), port))
        while 'Connected' not in client.cmd(cmd):
            output('waiting for', server,
                   'to listen on port', port, '\n')
        sleep(.5)

    def configure_dp(self, thrift_port):
        cmd = ["simple_switch_CLI","--thrift-port", str(thrift_port)]
        with open("queue_setup_commands.txt", "r") as f:
            print " ".join(cmd)
            subprocess.Popen(cmd, stdin=f).wait()
        sleep(1)

    # def run_controller(self, json_file):
    #     p4info_file = json_file.replace("json","p4info")
    #     cmd = ["./controller_server.py", "--p4info", p4info_file, "--bmv2-json", json_file]
    #     subprocess.Popen(cmd)
    #     sleep(5)

    def configure_mtu(self):
        subprocess.Popen("sudo ifconfig s1-eth1 mtu 1550; sudo ifconfig s1-eth2 mtu 1550",
                         shell=True).wait()
        sleep(1)

    def create_scenario(self):
        """Sets up the mininet instance, programs the switches"""

        print "## Initializing mininet with the topology specified by the config"
        # Initialize mininet with the topology specified by the config
        self.create_network()
        self.net.start()
        sleep(1)

        # some programming that must happen after the net has started
        self.program_hosts()

        # wait for that to finish. Not sure how to do this better
        sleep(1)

        for s in self.net.switches:
            s.describe()
        for h in self.net.hosts:
            h.describe()

        # wait for that to finish. Not sure how to do this better
        sleep(1)

    def create_sw_config_json(self, metadata):
        scenario = metadata["scenario"]
        self.sw_config = {
            "target": "bmv2",
            "p4info": self.switch_json[scenario].replace("json", "p4info"),
            "bmv2_json": self.switch_json[scenario],
            "table_entries": []
        }
        classifier_table_entry_1 = {
            "table": "MyIngress.sfc_classifier",
            "match": {
                "hdr.ipv4.srcAddr": ["10.0.1.1",32]
            },
            "action_name": "MyIngress.sfc_encapsulate",
            "action_params": {
                "spi": 1,
                "si": 255
            }
        }
        classifier_table_entry_2 = {
            "table": "MyIngress.sfc_classifier",
            "match": {
                "hdr.ipv4.srcAddr": ["10.0.1.2",32]
            },
            "action_name": "MyIngress.sfc_encapsulate",
            "action_params": {
                "spi": 2,
                "si": 255
            }
        }
        sff_table_entry_1 = {
            "table": "MyIngress.sfc_sf_forwarder",
            "match": {
                "hdr.nsh_sp.spi": 1,
                "hdr.nsh_sp.si": 255
            },
            "action_name": "MyIngress.sfc_desencapsulate",
            "action_params": {}
        }
        sff_table_entry_2 = {
            "table": "MyIngress.sfc_sf_forwarder",
            "match": {
                "hdr.nsh_sp.spi": 2,
                "hdr.nsh_sp.si": 255
            },
            "action_name": "MyIngress.sfc_desencapsulate",
            "action_params": {}
        }
        ipv4_lpm_table_entry_1 = {
            "table": "MyIngress.ipv4_lpm",
            "match": {
                "hdr.ipv4.dstAddr": ["10.0.1.1", 32]
            },
            "action_name": "MyIngress.ipv4_forward",
            "action_params": {
                "dstAddr": "00:00:00:00:01:01",
                "port": 1
            }
        }
        ipv4_lpm_table_entry_2 = {
            "table": "MyIngress.ipv4_lpm",
            "match": {
                "hdr.ipv4.dstAddr": ["10.0.1.2", 32]
            },
            "action_name": "MyIngress.ipv4_forward",
            "action_params": {
                "dstAddr": "00:00:00:00:01:02",
                "port": 2
            }
        }
        self.sw_config["table_entries"].append(classifier_table_entry_1)
        self.sw_config["table_entries"].append(classifier_table_entry_2)
        self.sw_config["table_entries"].append(sff_table_entry_1)
        self.sw_config["table_entries"].append(sff_table_entry_2)
        self.sw_config["table_entries"].append(ipv4_lpm_table_entry_1)
        self.sw_config["table_entries"].append(ipv4_lpm_table_entry_2)

    def create_sw_config_flows_json(self, metadata):
        num_flows = metadata["num_flows"]
        spi = 1
        si = 255
        src_ip_addr = "10.0.1.1"
        dst_ip_addr = "10.0.1.2"
        src_port = first_src_port
        dst_port = first_dst_port
        for i in xrange(num_flows):
            table_entry = {
                "table": "MyIngress.sfc_mon",
                "match": {
                    "hdr.nsh_sp.spi": spi,
                    "hdr.nsh_sp.si": si,
                    "hdr.ipv4.srcAddr": [src_ip_addr,"255.255.255.255"],
                    "hdr.ipv4.dstAddr": [dst_ip_addr,"255.255.255.255"],
                    "hdr.udp.srcPort": src_port,
                    "hdr.udp.dstPort": dst_port
                },
                "action_name": "MyIngress.update_stats",
                "action_params": {}
            }
            self.sw_config["table_entries"].append(table_entry)
            src_port += 1

    def create_sw_config_file(self, metadata):
        scenario = metadata["scenario"]
        num_flows = metadata["num_flows"]
        sw_config_file = "results/flows/"+scenario+"/swconfig-" + scenario + "-" + str(num_flows) + ".txt"
        with open(sw_config_file, 'w') as file:
            file.write(json.dumps(self.sw_config))
        return sw_config_file

    def run_iperf_measurement(self, net, client_name, server_name):
        sender = self.net.getNodeByName(client_name)
        recvr = self.net.getNodeByName(server_name)

        print "- Starting Iperf Server"
        out = recvr.cmd("iperf -s &")
        print out
        self.waitListening(sender, recvr, 5001)
        print "- Running Iperf Client"
        sender.sendCmd("iperf -f m -c %s -t %s" % (recvr.IP(), str(round_time_iperf)))
        out = sender.waitOutput()
        print out
        print "- Stopping Iperf Server"
        subprocess.Popen("pgrep -f iperf | sudo xargs kill -9", shell=True).wait()
        sleep(1)

        #res = re.findall(r"(\d+) Mbits/sec", out)
        res = re.findall(r"(\d+(?:\.\d+)?) Mbits/sec", out)
        return res[-1]

    def run_ditg_measurement(self, client_name, server_name, metadata):
        sender = self.net.getNodeByName(client_name)
        recvr = self.net.getNodeByName(server_name)
        packet_size = metadata["packet_size"]
        rate_pps = metadata["rate_pps"]
        dport = first_dst_port
        f = open(metadata["ditg-files"]["clients"], "w+")
        for i in xrange(1):
            line = "-a " + str(recvr.IP()) + " -m owdm -rp " + str(dport) + " -t " + str(
                round_time_ditg) + " -c " + str(packet_size) + " -C " + str(rate_pps)
            f.write(line)
            f.write("\n")
            dport+=1
        f.close()
        cmd_itgsend = "ITGSend %s -l %s -x %s" % (metadata["ditg-files"]["clients"], metadata["ditg-files"]["sender"], metadata["ditg-files"]["receiver"])
        cmd_itgdec = "ITGDec %s > %s" % (metadata["ditg-files"]["receiver"], metadata["ditg-files"]["summary"])
        print
        print "- Starting ITGRecv"
        out = recvr.cmd("ITGRecv &")
        print out
        self.waitListening(sender, recvr, 9000)
        print "- Running ITGSend"
        print cmd_itgsend
        sender.sendCmd(cmd_itgsend)
        out = sender.waitOutput()
        print out
        print "- Stopping ITGRecv"
        subprocess.Popen("pgrep -f ITGRecv | sudo xargs kill -9", shell=True).wait()
        sleep(1)
        print
        print "- Running ITGDec"
        print cmd_itgdec
        sender.sendCmd(cmd_itgdec)
        out = sender.waitOutput()
        print out

    def run_iperf_experiment(self,metadata):
        scenario = metadata["scenario"]
        num_flows = metadata["num_flows"]
        metadata["iperf-file"] = "results/raw/" + scenario + "/iperf-" + scenario + "-" + str(
            num_flows) + ".txt"
        f = open(metadata["iperf-file"], "w+")
        for i in xrange(num_rounds):
            round = i + 1
            print
            print "## Running Iperf measurement {} of {}".format(round, num_rounds)
            print
            print "- Running Simple Controller to populate P4 Tables"
            self.program_switch_p4runtime("s1",metadata["sw_config"])
            sleep(5)
            print
            print("- Evaluating reachability between hosts")
            self.net.pingAll()
            sleep(1)
            line = self.run_iperf_measurement(self.net, "h1", "h2")
            f.write(line)
            f.write("\n")
            sleep(1)
        f.close()

    def run_ditg_experiment(self, metadata):
        scenario = metadata["scenario"]
        packet_size = str(metadata["packet_size"])
        num_flows = metadata["num_flows"]

        for i in xrange(num_rounds):
            round = i + 1
            print
            print "## Running D-ITG measurement {} of {}".format(round, num_rounds)
            print
            print "- Running Simple Controller to populate P4 Tables"
            self.program_switch_p4runtime("s1",metadata["sw_config"])
            sleep(5)
            print
            print("- Evaluating reachability between hosts")
            self.net.pingAll()
            sleep(1)
            files = {}
            files["clients"] = "results/flows/"+scenario+"/multiple-" + scenario + "-" + packet_size + "-" + str(
                num_flows) + "-" + str(round) + ".txt"
            files["sender"] = "results/raw/"+scenario+"/sender-" + scenario + "-" + packet_size + "-" + str(num_flows) + "-" + str(
                round) + ".txt"
            files["receiver"] = "results/raw/"+scenario+"/receiver-" + scenario + "-" + packet_size + "-" + str(
                num_flows) + "-" + str(round) + ".txt"
            files["summary"] = "results/raw/"+scenario+"/summary-" + scenario + "-" + packet_size + "-" + str(
                num_flows) + "-" + str(round) + ".txt"
            metadata["ditg-files"] = files
            self.run_ditg_measurement("h1","h2", metadata)
            sleep(1)

    def run_experiment(self):
        subprocess.Popen("rm -rf results/raw results/flows", shell=True).wait()
        subprocess.Popen("mkdir -p results/raw results/flows", shell=True).wait()
        print
        print "###### Creating Mininet Topology ######"
        self.create_scenario()
        print
        print "###### Configuring MTU to 1550 ######"
        self.configure_mtu()
        for scenario in self.switch_json:
            print
            print
            print "############################################"
            print "######## SCENARIO: "+scenario+" #######"
            print "############################################"
            subprocess.Popen("mkdir -p results/raw/"+scenario+" results/flows/"+scenario, shell=True).wait()
            print
            print("###### Running Experiments ######")
            for y in num_flows:
                metadata = {"scenario": scenario, "num_flows": y, "ditg-files": {}}
                self.create_sw_config_json(metadata)
                if (scenario == "sfc_p4tables"):
                    self.create_sw_config_flows_json(metadata)
                metadata["sw_config"] = self.create_sw_config_file(metadata)
                if (scenario == "sfc_p4tables") or (y == fixed_num_flows):
                    self.run_iperf_experiment(metadata)
                    for x in packet_size:
                        packet_size_bits = x * 8
                        rate_pps = rate_bits / packet_size_bits
                        print
                        print "## PACKET SIZE: " + str(x) + " --- NUM. ACTIVATED FLOWS: " + str(y) + " --- RATE (PPS): " + str(
                            rate_pps) + " ####"
                        metadata["packet_size"] = x
                        metadata["rate_pps"] = rate_pps
                        self.run_ditg_experiment(metadata)
            subprocess.Popen("rm -rf results/raw/"+scenario+"/sender* results/raw/"+scenario+"/receiver*", shell=True).wait()
        self.net.stop()
        subprocess.Popen("sudo mn -c", shell=True).wait()
        subprocess.Popen("rm -rf build", shell=True).wait()

    def parse_links(self, unparsed_links):
        """ Given a list of links descriptions of the form [node1, node2, latency, bandwidth]
            with the latency and bandwidth being optional, parses these descriptions
            into dictionaries and store them as self.links
        """
        links = []
        for link in unparsed_links:
            # make sure each link's endpoints are ordered alphabetically
            s, t, = link[0], link[1]
            if s > t:
                s,t = t,s

            link_dict = {'node1':s,
                        'node2':t,
                        'latency':'0ms',
                        'bandwidth':None
                        }
            if len(link) > 2:
                link_dict['latency'] = self.formatLatency(link[2])
            if len(link) > 3:
                link_dict['bandwidth'] = link[3]

            if link_dict['node1'][0] == 'h':
                assert link_dict['node2'][0] == 's', 'Hosts should be connected to switches, not ' + str(link_dict['node2'])
            links.append(link_dict)
        return links


    def create_network(self):
        """ Create the mininet network object, and store it as self.net.

            Side effects:
                - Mininet topology instance stored as self.topo
                - Mininet instance stored as self.net
        """
        self.logger("Building mininet topology.")

        self.topo = ExperimentTopo(self.hosts, self.switches.keys(), self.links, self.log_dir)

        switchClass = configureP4Switch(
            sw_path=self.bmv2_exe)

        self.net = Mininet(topo = self.topo,
                      link = TCLink,
                      host = P4Host,
                      switch = switchClass,
                      controller = None)


    def program_switch_p4runtime(self, sw_name, sw_config_file):
        """ This method will use P4Runtime to program the switch using the
            content of the runtime JSON file as input.
        """
        sw_obj = self.net.get(sw_name)
        grpc_port = sw_obj.grpc_port
        device_id = sw_obj.device_id
        print('Configuring switch %s using P4Runtime with file %s' % (sw_name, sw_config_file))
        with open(sw_config_file, 'r') as sw_conf_file:
            outfile = '%s/%s-p4runtime-requests.txt' % (self.log_dir, sw_name)
            p4runtime_lib.simple_controller.program_switch(
                addr='127.0.0.1:%d' % grpc_port,
                device_id=device_id,
                sw_conf_file=sw_conf_file,
                workdir=os.getcwd(),
                proto_dump_fpath=outfile)

    def program_hosts(self):
        """ Adds static ARP entries and default routes to each mininet host.

            Assumes:
                - A mininet instance is stored as self.net and self.net.start() has
                  been called.
        """
        for host_name in self.topo.hosts():
            h = self.net.get(host_name)
            h_iface = h.intfs.values()[0]
            link = h_iface.link

            sw_iface = link.intf1 if link.intf1 != h_iface else link.intf2
            # phony IP to lie to the host about
            host_id = int(host_name[1:])
            sw_ip = '10.0.%d.254' % host_id

            # Ensure each host's interface name is unique, or else
            # mininet cannot shutdown gracefully
            h.defaultIntf().rename('%s-eth0' % host_name)
            # static arp entries and default routes
            h.cmd('arp -i %s -s %s %s' % (h_iface.name, sw_ip, sw_iface.mac))
            h.cmd('ethtool --offload %s rx off tx off' % h_iface.name)
            h.cmd('ip route add %s dev %s' % (sw_ip, h_iface.name))
            h.setDefaultRoute("via %s" % sw_ip)

            if (host_name == "h1"):
                h.setARP('10.0.1.2','00:00:00:00:01:02')
            elif (host_name == "h2"):
                h.setARP('10.0.1.1', '00:00:00:00:01:01')

def get_args():
    cwd = os.getcwd()
    default_logs = os.path.join(cwd, 'logs')
    default_pcaps = os.path.join(cwd, 'pcaps')
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--quiet', help='Suppress log messages.',
                        action='store_true', required=False, default=False)
    parser.add_argument('-t', '--topo', help='Path to topology json',
                        type=str, required=False, default='./topology.json')
    parser.add_argument('-l', '--log-dir', type=str, required=False, default=default_logs)
    parser.add_argument('-p', '--pcap-dir', type=str, required=False, default=default_pcaps)
    parser.add_argument('-x', '--switch-json-scenario1', type=str, required=False)
    parser.add_argument('-y', '--switch-json-scenario2', type=str, required=False)
    parser.add_argument('-z', '--switch-json-scenario3', type=str, required=False)
    parser.add_argument('-b', '--behavioral-exe', help='Path to behavioral executable',
                                type=str, required=False, default='simple_switch')
    return parser.parse_args()


if __name__ == '__main__':
    # from mininet.log import setLogLevel
    # setLogLevel("info")

    args = get_args()
    experiment = ExperimentRunner(args.topo, args.log_dir, args.pcap_dir,
                              args.switch_json_scenario1, args.switch_json_scenario2, args.switch_json_scenario3, args.behavioral_exe, args.quiet)

    experiment.run_experiment()

