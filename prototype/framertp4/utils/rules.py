def generate_icmp_rule(srcAddr,dstAddr):
    table_id = 0
    rule = {
      "match_fields": {
        "hdr.ipv4.srcAddr": [srcAddr, "255.255.255.255"],
        "hdr.ipv4.dstAddr": [dstAddr, "255.255.255.255"]
      },
      "action_name": "MyIngress.mark_as_suspicious",
      "action_params": {},
      "priority": 1
    }
    return table_id,rule

def generate_udp_rule(srcAddr,dstAddr,srcPort,dstPort):
    table_id = 1
    rule = {
      "match_fields": {
        "hdr.ipv4.srcAddr": [srcAddr, "255.255.255.255"],
        "hdr.ipv4.dstAddr": [dstAddr, "255.255.255.255"],
        "hdr.udp.srcPort": [srcPort, 65535],
        "hdr.udp.dstPort": [dstPort, 65535]
      },
      "action_name": "MyIngress.mark_as_suspicious",
      "action_params": {},
      "priority": 1
    }
    return table_id,rule

def generate_tcp_rule(srcAddr,dstAddr,srcPort,dstPort):
    table_id = 2
    rule = {
      "match_fields": {
        "hdr.ipv4.srcAddr": [srcAddr, "255.255.255.255"],
        "hdr.ipv4.dstAddr": [dstAddr, "255.255.255.255"],
        "hdr.tcp.srcPort": [srcPort, 65535],
        "hdr.tcp.dstPort": [dstPort, 65535]
      },
      "action_name": "MyIngress.mark_as_suspicious",
      "action_params": {},
      "priority": 1
    }
    return table_id,rule