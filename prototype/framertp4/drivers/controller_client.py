from xmlrpc.client import ServerProxy, Fault, ProtocolError, ResponseError
import threading

class RTP4ClientController():

    def __init__(self):
        self.conn = dict()
        self.servers = []
        self.up_servers = []
        self.down_servers = []
        self.firstTime = True

    def addUPServer(self, server_name):
        print ("Server " + server_name + " up!")
        self.up_servers.append(server_name)
        if server_name in self.down_servers:
            self.down_servers.remove(server_name)

    def addDownServer(self, server_name):
        print ("Server " + server_name + " down!")
        self.down_servers.append(server_name)
        if server_name in self.up_servers:
            self.up_servers.remove(server_name)

    def connectServer(self, server_name):
        try:
            self.conn[server_name] = ServerProxy('http://' + server_name + ':8000')
            self.addUPServer(server_name)
            return True
        except Exception as err:
            print("Error accessing " + server_name)
            print("Message   :", err)
            self.addDownServer(server_name)
        return False

    def connectServers(self,servers):
        for server_name in servers:
            self.connectServer(server_name)

    def tryConnectDownServers(self):
        for server_name in self.down_servers:
            self.connectServer(server_name)

    def getUpServers(self):
        return self.up_servers

    def getDownServers(self):
        return self.down_servers

    # def writeMaliciousRulePerControllerServer(self,server_name,proto, src_ip_range,dst_ip_range,src_port_range,dst_port_range):
    #     # Get remote data from server
    #     if self.conn[server_name] is not None:
    #         try:
    #             response = self.conn[server_name].write_malicious_rule(proto,src_ip_range,dst_ip_range,src_port_range,dst_port_range)
    #             print response
    #         except (xmlrpclib.Fault, xmlrpclib.ProtocolError, xmlrpclib.ResponseError) as err:
    #             print("A fault occurred")
    #             print("Fault code: " + str(err.faultCode))
    #             print ("Fault string: " + err.faultString)
    #             # In case of exception in the connection, return the server to the list of down servers
    #             self.addDownServer(server_name)
    #             return False
    #     else:
    #         print("ERROR: The stats from server " + server_name + " cannot be recovered. It does not have a valid connection.")
    #         self.addDownServer(server_name)

    # def readSwitchesCountersPerControllerServer(self,server_name):
    #     # Get remote data from server
    #     if self.conn[server_name] is not None:
    #         try:
    #             remote_counters = self.conn[server_name].read_switches_counters()
    #             print remote_counters
    #         except (xmlrpclib.Fault, xmlrpclib.ProtocolError, xmlrpclib.ResponseError) as err:
    #             print("A fault occurred")
    #             print("Fault code: " + str(err.faultCode))
    #             print ("Fault string: " + err.faultString)
    #             # In case of exception in the connection, return the server to the list of down servers
    #             self.addDownServer(server_name)
    #             return False
    #     else:
    #         print("ERROR: The stats from server " + server_name + " cannot be recovered. It does not have a valid connection.")
    #         self.addDownServer(server_name)
    #
    # def readSwitchesCounters(self):
    #     for server_name in self.up_servers:
    #         self.readSwitchesCountersPerControllerServer(server_name)

    # def writeMaliciousRule(self,proto,src_ip_range,dst_ip_range,src_port_range = None,dst_port_range = None):
    #     for server_name in self.up_servers:
    #         self.writeMaliciousRulePerControllerServer(server_name,proto, src_ip_range,dst_ip_range,src_port_range,dst_port_range)

    def addTableRulePerController(self, server_name, table_name, rule):
        # Get remote data from server
        if self.conn[server_name] is not None:
            try:
                response = self.conn[server_name].write_rule(table_name, rule)
                return response
            except (Fault, ProtocolError, ResponseError) as err:
                print("A fault occurred")
                print("Fault code: " + str(err.faultCode))
                print ("Fault string: " + err.faultString)
                # In case of exception in the connection, return the server to the list of down servers
                self.addDownServer(server_name)
                return False
        else:
            print("ERROR: The stats from server " + server_name + " cannot be recovered. It does not have a valid connection.")
            self.addDownServer(server_name)

    def addTableRule(self, table_name, rule):
        full_response = True
        for server_name in self.up_servers:
            response = self.addTableRulePerController(server_name, table_name, rule)
            full_response = full_response & response
        return full_response

    def deleteTableRulePerController(self, server_name, table_name, rule):
        # Get remote data from server
        if self.conn[server_name] is not None:
            try:
                response = self.conn[server_name].delete_rule(table_name, rule)
                return response
            except (Fault, ProtocolError, ResponseError) as err:
                print("A fault occurred")
                print("Fault code: " + str(err.faultCode))
                print ("Fault string: " + err.faultString)
                # In case of exception in the connection, return the server to the list of down servers
                self.addDownServer(server_name)
                return False
        else:
            print("ERROR: The stats from server " + server_name + " cannot be recovered. It does not have a valid connection.")
            self.addDownServer(server_name)

    def deleteTableRule(self, table_name, rule):
        full_response = True
        for server_name in self.up_servers:
            response = self.deleteTableRulePerController(server_name, table_name, rule)
            full_response = full_response & response
        return full_response

    def listTableRulesPerController(self, server_name, table_name):
        # Get remote data from server
        if self.conn[server_name] is not None:
            try:
                response = self.conn[server_name].read_rules(table_name)
                return response
            except (Fault, ProtocolError, ResponseError) as err:
                print("A fault occurred")
                print("Fault code: " + str(err.faultCode))
                print ("Fault string: " + err.faultString)
                # In case of exception in the connection, return the server to the list of down servers
                self.addDownServer(server_name)
                return False
        else:
            print("ERROR: The stats from server " + server_name + " cannot be recovered. It does not have a valid connection.")
            self.addDownServer(server_name)

    def listTableRules(self, table_name):
        response = {}
        for server_name in self.up_servers:
            response[server_name] = self.listTableRulesPerController(server_name, table_name)
        return response

    def readSFCMonPerController(self, server_name):
        # Get remote data from server
        if self.conn[server_name] is not None:
            try:
                response = self.conn[server_name].read_sfcmon()
                for switch in response:
                    response[switch]["ctr_bytes"] = []
                    response[switch]["ctr_pkts"] = []
                    for element in response[switch]["ctr_packets"]:
                        response[switch]["ctr_bytes"].append(element["bytes"])
                        response[switch]["ctr_pkts"].append(element["packets"])
                    del response[switch]["ctr_packets"]
                return response
            except (Fault, ProtocolError, ResponseError) as err:
                print("A fault occurred")
                print("Fault code: " + str(err.faultCode))
                print ("Fault string: " + err.faultString)
                # In case of exception in the connection, return the server to the list of down servers
                self.addDownServer(server_name)
                return False
        else:
            print("ERROR: The stats from server " + server_name + " cannot be recovered. It does not have a valid connection.")
            self.addDownServer(server_name)

    def readSFCMon(self):
        response = {}
        for server_name in self.up_servers:
            response[server_name] = self.readSFCMonPerController(server_name)
        return response

    def resetSFCMonPerController(self, server_name):
        # Get remote data from server
        if self.conn[server_name] is not None:
            try:
                response = self.conn[server_name].reset_sfcmon()
                return response
            except (Fault, ProtocolError, ResponseError) as err:
                print("A fault occurred")
                print("Fault code: " + str(err.faultCode))
                print ("Fault string: " + err.faultString)
                # In case of exception in the connection, return the server to the list of down servers
                self.addDownServer(server_name)
                return False
        else:
            print("ERROR: The stats from server " + server_name + " cannot be recovered. It does not have a valid connection.")
            self.addDownServer(server_name)

    def resetSFCMon(self):
        full_response = True
        for server_name in self.up_servers:
            response = self.resetSFCMonPerController(server_name)
            full_response = full_response & response
        return full_response

    def startClientController(self,servers):
        if self.firstTime:
            self.connectServers(servers)
            self.firstTime = False
            threading.Timer(5, self.tryConnectDownServers).start()
