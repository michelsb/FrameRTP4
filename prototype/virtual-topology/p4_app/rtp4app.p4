/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

#include "includes/headers/ethernet_hdr.p4"
#include "includes/headers/ipv4_hdr.p4"
#include "includes/headers/icmp_hdr.p4"
#include "includes/headers/udp_hdr.p4"
#include "includes/headers/tcp_hdr.p4"

// NSH headers
#include "includes/headers/nsh/nsh_tunnel_hdr.p4"
#include "includes/headers/nsh/nsh_base_hdr.p4"
#include "includes/headers/nsh/nsh_sp_hdr.p4"

/*************************************************************************
************************** MONITORING SYSTEM  ****************************
*************************************************************************/

#include "includes/rtp4mon_agent.p4"

/*************************************************************************
*********************** CONSTANTS AND NEW TYPES  **************************
*************************************************************************/

#include "includes/types.p4"

const bit<16> TYPE_IPV4 = 0x800;
const bit<4> NORMAL_STATE = 1;
const bit<4> MALICIOUS_STATE = 2;

const bit<16> TYPE_NSH = 0x1212;
typedef bit<24> nshSPI_t;
typedef bit<8> nshSI_t;

/*************************************************************************
***************************** STRUCTURES  ********************************
*************************************************************************/

struct state_metadata_t {
    bit<4> state;
}

struct metadata {
    state_metadata_t state_m;
    rtp4mon_metadata_t rtp4mon_m;
}

struct headers {
    ethernet_t   ethernet;
    nsh_tunnel_t nsh_tunnel;
    nsh_sp_t     nsh_sp;
    nsh_base_t   nsh_base;
    ipv4_t       ipv4;
    icmp_t       icmp;
    udp_t        udp;
    tcp_t        tcp;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_NSH: parse_nsh_sp;
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_nsh_sp {
        packet.extract(hdr.nsh_sp);
        transition parse_nsh_base;
    }

    state parse_nsh_base {
        packet.extract(hdr.nsh_base);
        transition parse_nsh_tunnel;
    }

    state parse_nsh_tunnel {
        packet.extract(hdr.nsh_tunnel);
        transition select(hdr.nsh_tunnel.proto_id) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            8w0x1: parse_icmp;
            8w0x6: parse_tcp;
            8w0x11: parse_udp;
            default: accept;
        }
    }

    state parse_icmp {
        packet.extract(hdr.icmp);
        transition accept;
    }

    state parse_udp {
        packet.extract(hdr.udp);
        transition accept;
    }

    state parse_tcp {
        packet.extract(hdr.tcp);
        transition accept;
    }

}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    /* Marked packets */
    counter(1, CounterType.packets_and_bytes) ctr_normal;
    counter(1, CounterType.packets_and_bytes) ctr_suspicious;
    //counter(1, CounterType.packets_and_bytes) ctr_hh;

    action drop() {
        mark_to_drop();
    }

    action mark_as_normal() {
        meta.state_m.state = NORMAL_STATE;
    }

    action mark_as_suspicious() {
        meta.state_m.state = MALICIOUS_STATE;
    }

    table idps_icmp_ternary {
        key = {
            hdr.ipv4.srcAddr: ternary;
            hdr.ipv4.dstAddr: ternary;
        }
        actions = {
            mark_as_normal;
            mark_as_suspicious;
            NoAction;
        }
        size = 1024;
        default_action = mark_as_normal();
    }

    table idps_udp_ternary {
        key = {
            hdr.ipv4.srcAddr: ternary;
            hdr.ipv4.dstAddr: ternary;
            hdr.udp.srcPort:  ternary;
            hdr.udp.dstPort:  ternary;
        }
        actions = {
            mark_as_normal;
            mark_as_suspicious;
            NoAction;
        }
        size = 1024;
        default_action = mark_as_normal();
    }

    table idps_tcp_ternary {
        key = {
            hdr.ipv4.srcAddr: ternary;
            hdr.ipv4.dstAddr: ternary;
            hdr.tcp.srcPort:  ternary;
            hdr.tcp.dstPort:  ternary;
        }
        actions = {
            mark_as_normal;
            mark_as_suspicious;
            NoAction;
        }
        size = 1024;
        default_action = mark_as_normal();
    }

    action sfc_encapsulate(nshSPI_t spi, nshSI_t si) {
        hdr.ethernet.etherType = TYPE_NSH;
        hdr.nsh_base.setValid();
        hdr.nsh_sp.setValid();
        hdr.nsh_base.version =0x0;
        hdr.nsh_base.ttl = 63;
        hdr.nsh_base.length = 0x2; //
        hdr.nsh_base.mdtype = 0x2; // This does not mandate any headers beyond the Base Header and Service Path Header, but may contain optional Variable-Length Context Header(s).
        hdr.nsh_base.protocol = 0x3; // ethernet
        hdr.nsh_sp.spi = spi;
        hdr.nsh_sp.si = si;
    }

    action sfc_forward(bit<16> dst_id, bit<1> is_sff) {
        hdr.nsh_tunnel.setValid();
        hdr.nsh_tunnel.dst_id = dst_id;
        hdr.nsh_tunnel.proto_id = TYPE_IPV4;
        hdr.nsh_base.ttl = (is_sff == 1) ? hdr.nsh_base.ttl-1 : hdr.nsh_base.ttl;
    }

    action sfc_desencapsulate() {
        hdr.ethernet.etherType = TYPE_IPV4;
        hdr.nsh_base.setInvalid();
        hdr.nsh_sp.setInvalid();
        hdr.nsh_tunnel.setInvalid();
    }

    action nsh_tunnel_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    table sfc_classifier {
         key = {
            hdr.ipv4.srcAddr: lpm;
        }
        actions = {
            sfc_encapsulate;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    table sfc_sf_forwarder {
         key = {
            hdr.nsh_sp.spi: exact;
            hdr.nsh_sp.si: exact;
        }
        actions = {
            sfc_forward;
            sfc_desencapsulate;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    table nsh_tunnel_exact {
        key = {
            hdr.nsh_tunnel.dst_id: exact;
        }
        actions = {
            nsh_tunnel_forward;
            drop;
        }
        size = 1024;
        default_action = drop();
    }

    apply {
        //ctr_hh.count(0);
        if (hdr.ipv4.isValid() && hdr.ipv4.ttl > 0){

            if (hdr.icmp.isValid()) {
                idps_icmp_ternary.apply();
            } else {
                if (hdr.udp.isValid()) {
                    idps_udp_ternary.apply();
                } else {
                    if (hdr.tcp.isValid()) {
                        idps_tcp_ternary.apply();
                    }
                }
            }
            if (meta.state_m.state == NORMAL_STATE) {
                ctr_normal.count(1);
            }
            if (meta.state_m.state == MALICIOUS_STATE) {
                ctr_suspicious.count(2);
                drop();
            }

            if (!hdr.nsh_base.isValid()) {
                sfc_classifier.apply();
            }

            if (hdr.nsh_base.isValid()) {
                if (hdr.nsh_base.ttl == 0 || hdr.nsh_sp.si == 0){
                    drop();
                } else {
                    /************MONITOR*************/
                    bit<16> srcPort = 0;
                    bit<16> dstPort = 0;
                    if (hdr.udp.isValid()) {
                           srcPort = hdr.udp.srcPort;
                           dstPort = hdr.udp.dstPort;
                    } else {
                       if (hdr.tcp.isValid()) {
                           srcPort = hdr.tcp.srcPort;
                           dstPort = hdr.tcp.dstPort;
                        }
                    }
                    if (srcPort != 0) {
                        create_flow_id_cm_sketch(meta.rtp4mon_m,hdr.ipv4.srcAddr,hdr.nsh_sp.spi,hdr.nsh_sp.si);
                        update_cm_sketch(meta.rtp4mon_m);
                        if (meta.rtp4mon_m.ctr_packets >= THRESHOLD_MIN_PKTS) {
                            estimate_cm_sketch(meta.rtp4mon_m);
                            if (meta.rtp4mon_m.is_hh == 1) {
                                create_flow_id_bf(meta.rtp4mon_m,hdr.ipv4.srcAddr,hdr.ipv4.dstAddr,srcPort,dstPort,hdr.ipv4.protocol,hdr.nsh_sp.spi,hdr.nsh_sp.si);
                                membership_query_bf(meta.rtp4mon_m);
                                if (meta.rtp4mon_m.is_stored == 0) {
                                    add_iblt_entry(meta.rtp4mon_m,standard_metadata.ingress_global_timestamp);
                                }
                                update_iblt_entry(meta.rtp4mon_m);
                            }
                        }
                    }
                    /**********************************/
                    sfc_sf_forwarder.apply();
                }
            }

            if (!hdr.nsh_tunnel.isValid()) {
                // Process only non-tunneled IPv4 packets
                ipv4_lpm.apply();
            } else {
                nsh_tunnel_exact.apply();
            }
        }else{
            drop();
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {  }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
     apply {
	update_checksum(
	    hdr.ipv4.isValid(),
            { hdr.ipv4.version,
	      hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.nsh_sp);
        packet.emit(hdr.nsh_base);
        packet.emit(hdr.nsh_tunnel);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.icmp);
        packet.emit(hdr.udp);
        packet.emit(hdr.tcp);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
