register<bit<48>>(16384) last_seen;

action get_inter_packet_gap(out bit<48> interval, bit<14> flow_id){
	bit<48> last_pkt_ts;
	/* Get the time the previous packet was seen */
	last_seen.read((bit<32>)flow_id,
	last_pkt_ts);
	/* Calculate the time interval */
	interval = standard_metadata.ingress_global_timestamp –
	last_pkt_ts;
	/* Update the register with the new timestamp */
	last_seen.write((bit<32>)flow_id,
	standard_metadata.ingress_global_timestamp);
}