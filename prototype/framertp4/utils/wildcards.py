import itertools
from utils.convert import convert_bin_to_ip

def diff_bin(a, b):
    diff = list()
    for i in range(len(a)):
        if a[i] != b[i]:
            diff.append(i)
    return diff

def permutation_pattern(pattern,maxWild):
    provisorySolution = []
    wildcards_position = [pos for pos,value in enumerate(pattern) if value == 2]
    comb_size = len(wildcards_position) - maxWild
    combs = itertools.combinations(wildcards_position,comb_size)
    for comb in combs:
        sample_pattern = [['0', '1'] if pos in comb else str(value) for pos,value in enumerate(pattern)]
        subset_provisorySolution = [''.join(lst) for lst in itertools.product(*sample_pattern)]
        provisorySolution.extend(subset_provisorySolution)
    return provisorySolution

def generate_patterns(pattern):
    a = [['0', '1'] if (c == '2') else c for c in pattern]
    b = [''.join(lst) for lst in itertools.product(*a)]
    return b

def generate_pattern_ports(pattern):
    a = [['0', '1'] if (c == '*') else c for c in pattern]
    b = [''.join(lst) for lst in itertools.product(*a)]
    return [int(i, 2) for i in b]

def generate_pattern_ips(pattern):
    a = [['0', '1'] if (c == '*') else c for c in pattern]
    b = [''.join(lst) for lst in itertools.product(*a)]
    return [convert_bin_to_ip(i) for i in b]

def count_pattern_elements(pattern):
    a = [['0', '1'] if (c == '*') else c for c in pattern]
    b = [''.join(lst) for lst in itertools.product(*a)]
    return len(b)

def convert_bin_to_value_mask(bin_value):
    value = bin_value.replace('*','0')
    mask = bin_value.replace('0','1').replace('*','0')
    return int(value,2),int(mask,2)
