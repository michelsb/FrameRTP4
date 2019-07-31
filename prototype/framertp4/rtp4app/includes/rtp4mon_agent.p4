

/*************************************************************************
*********************** CONSTANTS AND NEW TYPES  **************************
*************************************************************************/
typedef bit<64> flowIDCMS_t;
typedef bit<136> flowIDBF_t;
typedef bit<32> flowIDHash_t;
typedef bit<24> flowCount_t;

//const bit<32> CM_SKETCH_WIDTH_SIZE = 32w32;
//const bit<32> BF_SIZE = 32w1024;
//const bit<32> IBLT_SIZE = 32w32;
//const bit<8> THRESHOLD_HH = 8w4; // 6%

const bit<32> CM_SKETCH_WIDTH_SIZE = 32w5436;
// T = 10000000
// T/K = 10000 (0,1%)
// K = 1000
// e = 1/2K = 0,0005
// w = euler/e = 2,71/0,0005 = 5420
// NUM. Hash Functions = 5

const bit<32> BF_SIZE = 32w1500;
const bit<32> IBLT_SIZE = 32w245;
// We are considering N = 200
// BF_SIZE > 3*N
// IBLT_SIZE > 1,222N
// NUM. Hash Functions = 3

const bit<24> THRESHOLD_MIN_PKTS = 10w1000;
const bit<8> THRESHOLD_HH = 8w10;
// threshold = ctr_packets/2^n
// 1/2^n = 0.001 (0,1%)
// THRESHOLD_HH = n

/*************************************************************************
***************************** STRUCTURES  ********************************
*************************************************************************/

struct rtp4mon_metadata_t {

    // Flow ID
    flowIDBF_t flow_id_bf;
    flowIDCMS_t flow_id_cms;

    // Flow ID hash for CM Sketch
    flowIDHash_t cm_sketch_idx1;
    flowIDHash_t cm_sketch_idx2;
    flowIDHash_t cm_sketch_idx3;
    flowIDHash_t cm_sketch_idx4;
    flowIDHash_t cm_sketch_idx5;

    // CM Sketch Estimation
    flowCount_t ctr_packets;
    flowCount_t min_ctr_packets;
    // CM Sketch - Heavy Hitter Detection Result
    bit<1> is_hh;

    // Flow ID hash for Bloom Filter
    flowIDHash_t bf_idx1;
    flowIDHash_t bf_idx2;
    flowIDHash_t bf_idx3;

    // Bloom Filter - Membership Query Result
    bit<1> is_stored;

    // Flow ID hash for IBLT
    flowIDHash_t iblt_idx1;
    flowIDHash_t iblt_idx2;
    flowIDHash_t iblt_idx3;
}


/*************************************************************************
****************** CM SKETCH - HEAVY HITTER DETECTION   ******************
*************************************************************************/

register<flowCount_t>(CM_SKETCH_WIDTH_SIZE) cm_sketch_row1;
register<flowCount_t>(CM_SKETCH_WIDTH_SIZE) cm_sketch_row2;
register<flowCount_t>(CM_SKETCH_WIDTH_SIZE) cm_sketch_row3;
register<flowCount_t>(CM_SKETCH_WIDTH_SIZE) cm_sketch_row4;
register<flowCount_t>(CM_SKETCH_WIDTH_SIZE) cm_sketch_row5;
register<flowCount_t>(1) global_ctr_packets;
//register<flowCount_t>(1) threshold;

/*************************************************************************
*********************** BF - MEMBERSHIP FILTER   *************************
*************************************************************************/

register<bit<1>>(BF_SIZE) bf_flow_filter;

/*************************************************************************
*********************** IBLT - FLOW STATS TABLE   ************************
*************************************************************************/

register<bit<8>>(IBLT_SIZE) iblt_ctr_flows;
register<flowIDHash_t>(IBLT_SIZE) iblt_flow_xor_idx1;
register<flowIDHash_t>(IBLT_SIZE) iblt_flow_xor_idx2;
register<flowIDHash_t>(IBLT_SIZE) iblt_flow_xor_idx3;
register<bit<8>>(IBLT_SIZE) iblt_flow_xor_proto;
register<bit<32>>(IBLT_SIZE) iblt_flow_xor_srcAddr;
register<bit<32>>(IBLT_SIZE) iblt_flow_xor_dstAddr;
register<bit<16>>(IBLT_SIZE) iblt_flow_xor_srcPort;
register<bit<16>>(IBLT_SIZE) iblt_flow_xor_dstPort;
register<bit<24>>(IBLT_SIZE) iblt_flow_xor_spi;
register<bit<8>>(IBLT_SIZE) iblt_flow_xor_si;
//register<bit<32>>(METRICS_TABLE_SIZE) ctr_packets;
counter(IBLT_SIZE, CounterType.packets_and_bytes) iblt_ctr_packets;
register<bit<48>>(IBLT_SIZE) iblt_first_seen;

/*************************************************************************
******************************** ACTIONS *********************************
*************************************************************************/

/*Function to find minimum of x and y*/
/*public:
int min(int x, int y)
{
    return y ^ ((x ^ y) & -(x < y));
} */

/*Function to find maximum of x and y*/
/*int max(int x, int y)
{
    return x ^ ((x ^ y) & -(x < y));
}
};*/

action create_flow_id_cm_sketch (inout rtp4mon_metadata_t meta, in bit<32> srcAddr, in bit<24> spi, in bit<8> si) {
    meta.flow_id_cms = srcAddr ++ spi ++ si;
}

action create_flow_id_bf (inout rtp4mon_metadata_t meta, in bit<32> srcAddr, in bit<32> dstAddr, in bit<16> srcPort, in bit<16> dstPort, in bit<8> proto, in bit<24> spi, in bit<8> si) {
    meta.flow_id_bf = spi ++ si ++ srcAddr ++ dstAddr ++ srcPort ++ dstPort ++ proto;
}

action update_cm_sketch(inout rtp4mon_metadata_t meta) {
    global_ctr_packets.read(meta.ctr_packets,0);
    meta.ctr_packets = meta.ctr_packets+1;
    global_ctr_packets.write(0,meta.ctr_packets);

    hash(meta.cm_sketch_idx1, HashAlgorithm.my_hash1,
        32w0,
        {meta.flow_id_cms},
        CM_SKETCH_WIDTH_SIZE);
    hash(meta.cm_sketch_idx2, HashAlgorithm.my_hash2,
        32w0,
        {meta.flow_id_cms},
        CM_SKETCH_WIDTH_SIZE);
    hash(meta.cm_sketch_idx3, HashAlgorithm.my_hash3,
        32w0,
        {meta.flow_id_cms},
        CM_SKETCH_WIDTH_SIZE);
    hash(meta.cm_sketch_idx4, HashAlgorithm.my_hash4,
        32w0,
        {meta.flow_id_cms},
        CM_SKETCH_WIDTH_SIZE);
    hash(meta.cm_sketch_idx5, HashAlgorithm.my_hash5,
        32w0,
        {meta.flow_id_cms},
        CM_SKETCH_WIDTH_SIZE);

    flowCount_t ctr_x; flowCount_t ctr_y;

    cm_sketch_row1.read(ctr_x,meta.cm_sketch_idx1);
    ctr_x = ctr_x+1;
    cm_sketch_row1.write(meta.cm_sketch_idx1,ctr_x);
    cm_sketch_row2.read(ctr_y,meta.cm_sketch_idx2);
    ctr_y = ctr_y+1;
    cm_sketch_row2.write(meta.cm_sketch_idx2,ctr_y);
    ctr_x = (ctr_x < ctr_y) ? ctr_x : ctr_y;

    cm_sketch_row3.read(ctr_y,meta.cm_sketch_idx3);
    ctr_y = ctr_y+1;
    cm_sketch_row3.write(meta.cm_sketch_idx3,ctr_y);
    ctr_x = (ctr_x < ctr_y) ? ctr_x : ctr_y;

    cm_sketch_row4.read(ctr_y,meta.cm_sketch_idx4);
    ctr_y = ctr_y+1;
    cm_sketch_row4.write(meta.cm_sketch_idx4,ctr_y);
    ctr_x = (ctr_x < ctr_y) ? ctr_x : ctr_y;

    cm_sketch_row5.read(ctr_y,meta.cm_sketch_idx5);
    ctr_y = ctr_y+1;
    cm_sketch_row5.write(meta.cm_sketch_idx5,ctr_y);
    ctr_x = (ctr_x < ctr_y) ? ctr_x : ctr_y;

    meta.min_ctr_packets = ctr_x; // Saves the minimum
}

action estimate_cm_sketch(inout rtp4mon_metadata_t meta) {
    flowCount_t ctr_x; flowCount_t ctr_y;
    ctr_x = meta.min_ctr_packets;
    ctr_y = meta.ctr_packets >> THRESHOLD_HH;
    meta.is_hh = (ctr_x < ctr_y) ? 1w0 : 1w1;
}

action membership_query_bf(inout rtp4mon_metadata_t meta) {

    /* Hashes for SFCMonBF */
    hash(meta.bf_idx1, HashAlgorithm.my_hash1,
        32w0,
        {meta.flow_id_bf},
        BF_SIZE);
    hash(meta.bf_idx2, HashAlgorithm.my_hash2,
        32w0,
        {meta.flow_id_bf},
        BF_SIZE);
    hash(meta.bf_idx3, HashAlgorithm.my_hash3,
        32w0,
        {meta.flow_id_bf},
        BF_SIZE);

    /* Hashes for SFCMonIBLT */
    hash(meta.iblt_idx1, HashAlgorithm.my_hash4,
        32w0,
        {meta.flow_id_bf},
        IBLT_SIZE);
    hash(meta.iblt_idx2, HashAlgorithm.my_hash5,
        32w0,
        {meta.flow_id_bf},
        IBLT_SIZE);
    hash(meta.iblt_idx3, HashAlgorithm.my_hash6,
        32w0,
        {meta.flow_id_bf},
        IBLT_SIZE);

    bit<1> query_idx1; bit<1> query_idx2; bit<1> query_idx3;
    bf_flow_filter.read(query_idx1, meta.bf_idx1);
    bf_flow_filter.read(query_idx2, meta.bf_idx2);
    bf_flow_filter.read(query_idx3, meta.bf_idx3);
    meta.is_stored = query_idx1 & query_idx2 & query_idx3;
}

action add_iblt_entry(inout rtp4mon_metadata_t meta, in bit<48> timestamp) {

    bf_flow_filter.write(meta.bf_idx1, 0b1);
    bf_flow_filter.write(meta.bf_idx2, 0b1);
    bf_flow_filter.write(meta.bf_idx3, 0b1);

    bit<8> ctr_flows;

    /* Update ctr_flow */
    iblt_ctr_flows.read(ctr_flows,meta.iblt_idx1);
    iblt_ctr_flows.write(meta.iblt_idx1,ctr_flows+1);
    iblt_ctr_flows.read(ctr_flows,meta.iblt_idx2);
    iblt_ctr_flows.write(meta.iblt_idx2,ctr_flows+1);
    iblt_ctr_flows.read(ctr_flows,meta.iblt_idx3);
    iblt_ctr_flows.write(meta.iblt_idx3,ctr_flows+1);


    bit<48> first_seen;

    /* Update first_seen */
    iblt_first_seen.read(first_seen,meta.iblt_idx1);
    iblt_first_seen.write(meta.iblt_idx1,first_seen ^ timestamp);
    iblt_first_seen.read(first_seen,meta.iblt_idx2);
    iblt_first_seen.write(meta.iblt_idx2,first_seen ^ timestamp);
    iblt_first_seen.read(first_seen,meta.iblt_idx3);
    iblt_first_seen.write(meta.iblt_idx3,first_seen ^ timestamp);

    flowIDHash_t query_idx;

    /* Update flow_xor_idx1 */
    iblt_flow_xor_idx1.read(query_idx,meta.iblt_idx1);
    query_idx = query_idx ^ meta.iblt_idx1;
    iblt_flow_xor_idx1.write(meta.iblt_idx1,query_idx);
    iblt_flow_xor_idx1.read(query_idx,meta.iblt_idx2);
    query_idx = query_idx ^ meta.iblt_idx1;
    iblt_flow_xor_idx1.write(meta.iblt_idx2,query_idx);
    iblt_flow_xor_idx1.read(query_idx,meta.iblt_idx3);
    query_idx = query_idx ^ meta.iblt_idx1;
    iblt_flow_xor_idx1.write(meta.iblt_idx3,query_idx);

    /* Update flow_xor_idx2 */
    iblt_flow_xor_idx2.read(query_idx,meta.iblt_idx1);
    query_idx = query_idx ^ meta.iblt_idx2;
    iblt_flow_xor_idx2.write(meta.iblt_idx1,query_idx);
    iblt_flow_xor_idx2.read(query_idx,meta.iblt_idx2);
    query_idx = query_idx ^ meta.iblt_idx2;
    iblt_flow_xor_idx2.write(meta.iblt_idx2,query_idx);
    iblt_flow_xor_idx2.read(query_idx,meta.iblt_idx3);
    query_idx = query_idx ^ meta.iblt_idx2;
    iblt_flow_xor_idx2.write(meta.iblt_idx3,query_idx);

    /* Update flow_xor_idx3 */
    iblt_flow_xor_idx3.read(query_idx,meta.iblt_idx1);
    query_idx = query_idx ^ meta.iblt_idx3;
    iblt_flow_xor_idx3.write(meta.iblt_idx1,query_idx);
    iblt_flow_xor_idx3.read(query_idx,meta.iblt_idx2);
    query_idx = query_idx ^ meta.iblt_idx3;
    iblt_flow_xor_idx3.write(meta.iblt_idx2,query_idx);
    iblt_flow_xor_idx3.read(query_idx,meta.iblt_idx3);
    query_idx = query_idx ^ meta.iblt_idx3;
    iblt_flow_xor_idx3.write(meta.iblt_idx3,query_idx);

    bit<8> flow_proto = meta.flow_id_bf[7:0];
    bit<16> flow_dstPort = meta.flow_id_bf[23:8];
    bit<16> flow_srcPort = meta.flow_id_bf[39:24];
    bit<32> flow_dstAddr = meta.flow_id_bf[71:40];
    bit<32> flow_srcAddr = meta.flow_id_bf[103:72];
    bit<8> flow_si = meta.flow_id_bf[111:104];
    bit<24> flow_spi = meta.flow_id_bf[135:112];

    bit<8> query_proto;
    bit<16> query_dstPort;
    bit<16> query_srcPort;
    bit<32> query_dstAddr;
    bit<32> query_srcAddr;
    bit<8> query_si;
    bit<24> query_spi;

    iblt_flow_xor_proto.read(query_proto,meta.iblt_idx1);
    iblt_flow_xor_dstPort.read(query_dstPort,meta.iblt_idx1);
    iblt_flow_xor_srcPort.read(query_srcPort,meta.iblt_idx1);
    iblt_flow_xor_dstAddr.read(query_dstAddr,meta.iblt_idx1);
    iblt_flow_xor_srcAddr.read(query_srcAddr,meta.iblt_idx1);
    iblt_flow_xor_si.read(query_si,meta.iblt_idx1);
    iblt_flow_xor_spi.read(query_spi,meta.iblt_idx1);
    query_proto = flow_proto ^ query_proto;
    query_dstPort = flow_dstPort ^ query_dstPort;
    query_srcPort = flow_srcPort ^ query_srcPort;
    query_dstAddr = flow_dstAddr ^ query_dstAddr;
    query_srcAddr = flow_srcAddr ^ query_srcAddr;
    query_si = flow_si ^ query_si;
    query_spi = flow_spi ^ query_spi;
    iblt_flow_xor_proto.write(meta.iblt_idx1,query_proto);
    iblt_flow_xor_dstPort.write(meta.iblt_idx1,query_dstPort);
    iblt_flow_xor_srcPort.write(meta.iblt_idx1,query_srcPort);
    iblt_flow_xor_dstAddr.write(meta.iblt_idx1,query_dstAddr);
    iblt_flow_xor_srcAddr.write(meta.iblt_idx1,query_srcAddr);
    iblt_flow_xor_si.write(meta.iblt_idx1,query_si);
    iblt_flow_xor_spi.write(meta.iblt_idx1,query_spi);

    iblt_flow_xor_proto.read(query_proto,meta.iblt_idx2);
    iblt_flow_xor_dstPort.read(query_dstPort,meta.iblt_idx2);
    iblt_flow_xor_srcPort.read(query_srcPort,meta.iblt_idx2);
    iblt_flow_xor_dstAddr.read(query_dstAddr,meta.iblt_idx2);
    iblt_flow_xor_srcAddr.read(query_srcAddr,meta.iblt_idx2);
    iblt_flow_xor_si.read(query_si,meta.iblt_idx2);
    iblt_flow_xor_spi.read(query_spi,meta.iblt_idx2);
    query_proto = flow_proto ^ query_proto;
    query_dstPort = flow_dstPort ^ query_dstPort;
    query_srcPort = flow_srcPort ^ query_srcPort;
    query_dstAddr = flow_dstAddr ^ query_dstAddr;
    query_srcAddr = flow_srcAddr ^ query_srcAddr;
    query_si = flow_si ^ query_si;
    query_spi = flow_spi ^ query_spi;
    iblt_flow_xor_proto.write(meta.iblt_idx2,query_proto);
    iblt_flow_xor_dstPort.write(meta.iblt_idx2,query_dstPort);
    iblt_flow_xor_srcPort.write(meta.iblt_idx2,query_srcPort);
    iblt_flow_xor_dstAddr.write(meta.iblt_idx2,query_dstAddr);
    iblt_flow_xor_srcAddr.write(meta.iblt_idx2,query_srcAddr);
    iblt_flow_xor_si.write(meta.iblt_idx2,query_si);
    iblt_flow_xor_spi.write(meta.iblt_idx2,query_spi);

    iblt_flow_xor_proto.read(query_proto,meta.iblt_idx3);
    iblt_flow_xor_dstPort.read(query_dstPort,meta.iblt_idx3);
    iblt_flow_xor_srcPort.read(query_srcPort,meta.iblt_idx3);
    iblt_flow_xor_dstAddr.read(query_dstAddr,meta.iblt_idx3);
    iblt_flow_xor_srcAddr.read(query_srcAddr,meta.iblt_idx3);
    iblt_flow_xor_si.read(query_si,meta.iblt_idx3);
    iblt_flow_xor_spi.read(query_spi,meta.iblt_idx3);
    query_proto = flow_proto ^ query_proto;
    query_dstPort = flow_dstPort ^ query_dstPort;
    query_srcPort = flow_srcPort ^ query_srcPort;
    query_dstAddr = flow_dstAddr ^ query_dstAddr;
    query_srcAddr = flow_srcAddr ^ query_srcAddr;
    query_si = flow_si ^ query_si;
    query_spi = flow_spi ^ query_spi;
    iblt_flow_xor_proto.write(meta.iblt_idx3,query_proto);
    iblt_flow_xor_dstPort.write(meta.iblt_idx3,query_dstPort);
    iblt_flow_xor_srcPort.write(meta.iblt_idx3,query_srcPort);
    iblt_flow_xor_dstAddr.write(meta.iblt_idx3,query_dstAddr);
    iblt_flow_xor_srcAddr.write(meta.iblt_idx3,query_srcAddr);
    iblt_flow_xor_si.write(meta.iblt_idx3,query_si);
    iblt_flow_xor_spi.write(meta.iblt_idx3,query_spi);
}

action update_iblt_entry(inout rtp4mon_metadata_t meta) {
    iblt_ctr_packets.count(meta.iblt_idx1);
    iblt_ctr_packets.count(meta.iblt_idx2);
    iblt_ctr_packets.count(meta.iblt_idx3);
}


