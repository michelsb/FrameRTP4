from rtp4rules_generator import generate_values_with_wildcards
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

    #print(list_values)

    if type_field == "ip":
        size=32
        for value in list_values:
            bin_list.append(convert_ip_to_bin(value))
    elif type_field == "port":
        size=16
        for value in list_values:
            bin_list.append(convert_port_to_bin(value))

    #print("# " + str(datetime.datetime.now()) + " - Generating Wildcards")
    wildcards = generate_values_with_wildcards(bin_list, size)
    #print wildcards
    #print("# " + str(datetime.datetime.now()) + " - Wildcards generated")

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
    #print list_groups
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







