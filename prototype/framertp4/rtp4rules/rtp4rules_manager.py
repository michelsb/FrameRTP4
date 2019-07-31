import json
import pandas
from rtp4rules.rtp4rules_generator import generate_values_with_wildcards
from utils.convert import convert_ip_to_bin, convert_port_to_bin, convert_bin_to_ip
from utils.wildcards import generate_pattern_ips, generate_pattern_ports, convert_bin_to_value_mask

match_fields_type = {
        "hdr.ipv4.srcAddr": "ip",
        "hdr.ipv4.dstAddr": "ip",
        "hdr.tcp.srcPort": "port",
        "hdr.tcp.dstPort": "port"
        }

def convert_to_wildcards(df, field, type_field, list_groups=None):
    bin_list = []

    size = 0

    if (list_groups is None) or (len(list_groups) == 0):
        df_filtered = df[field]
    else:
        filter = df[list_groups[0][0]] == list_groups[0][1]
        for group in list_groups[1:]:
            filter = filter & (df[group[0]] == group[1])
        df_filtered = df[filter][field]

    list_values = df_filtered.drop_duplicates().sort_values(ascending=True).tolist()

    if type_field == "ip":
        size=32
        for value in list_values:
            bin_list.append(convert_ip_to_bin(value))
    elif type_field == "port":
        size=16
        for value in list_values:
            bin_list.append(convert_port_to_bin(value))

    wildcards = generate_values_with_wildcards(bin_list, size)

    replaceDict = {}
    if type_field == "ip":
        for pattern in wildcards:
            elements = generate_pattern_ips(pattern)
            replaceDict.update(dict(zip(elements,[pattern for i in range(0,len(elements))])))

    elif type_field == "port":
        for pattern in wildcards:
            elements = generate_pattern_ports(pattern)
            replaceDict.update(dict(zip(elements, [pattern for i in range(0, len(elements))])))

    df_filtered = df_filtered.map(replaceDict)
    df.update(df_filtered)

    return wildcards

def generate_flows_with_wildcards(df, cols, list_groups=None, index=0):
    col_name = cols[index][0]
    col_type = cols[index][1]
    if (list_groups is not None) and (len(list_groups) == 0):
        return
    elif index == (len(cols)-1):
        convert_to_wildcards(df, col_name, col_type, list_groups)
        return
    if list_groups is None:
        groups = convert_to_wildcards(df, col_name, col_type)
        list_groups = []
    else:
        groups = convert_to_wildcards(df, col_name, col_type, list_groups)
    index += 1
    for group in groups:
        generate_flows_with_wildcards(df,cols,list_groups+[(col_name,group)],index)

def generate_wildcarded_rtp4rules(rules):
    wildcarded_rules = []
    if len(rules) > 0:
        action_name = rules[0]["action_name"]
        action_params = rules[0]["action_params"]
        priority = rules[0]["priority"]
        flows = {}
        cols = []
        for rule in rules:
            for match_field in rule["match_fields"].keys():
                if match_field not in flows:
                    flows[match_field] = []
                    cols.append((match_field,match_fields_type[match_field]))
                value = rule["match_fields"][match_field][0]
                flows[match_field].append(value)
        df_flows = pandas.DataFrame(flows)
        #print(df_flows)
        generate_flows_with_wildcards(df_flows, cols, None, 0)
        df_flows = df_flows.drop_duplicates()
        #print(df_flows)
        for index, row in df_flows.iterrows():
            wildcarded_rule = {"match_fields":{},"action_name":str(action_name),
                               "action_params":action_params,"priority":priority}
            for col in cols:
                col_name = col[0]
                col_type = col[1]
                value, mask = convert_bin_to_value_mask(row[col_name])
                if col_type == "ip":
                    value = convert_bin_to_ip('{:032b}'.format(value))
                    mask = convert_bin_to_ip('{:032b}'.format(mask))
                wildcarded_rule["match_fields"][str(col_name)] = [value, mask]
            wildcarded_rules.append(wildcarded_rule)
    #print(wildcarded_rules)

    return wildcarded_rules