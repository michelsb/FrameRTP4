import struct

def convert_port_to_bin(port):
    return '{:016b}'.format(port)

def convert_ip_to_bin(ip):
    octets = map(int, ip.split('/')[0].split('.'))  # '1.2.3.4'=>[1, 2, 3, 4]
    binary = '{0:08b}{1:08b}{2:08b}{3:08b}'.format(*octets)
    range = int(ip.split('/')[1]) if '/' in ip else None
    return binary[:range] if range else binary

def convert_bin_to_ip(bin):
    first_octet = int(bin[0:8], 2)
    second_octet = int(bin[8:16], 2)
    third_octet = int(bin[16:24], 2)
    fourth_octet = int(bin[24:32], 2)
    return '%d.%d.%d.%d' % (first_octet, second_octet, third_octet, fourth_octet)

def convert_int_to_ip(ipnum):
    first_octet = int(ipnum / 16777216) % 256
    second_octet = int(ipnum / 65536) % 256
    third_octet = int(ipnum / 256) % 256
    fourth_octet = int(ipnum) % 256
    return '%(first_octet)s.%(second_octet)s.%(third_octet)s.%(fourth_octet)s' % locals()

def hex_to_i16(h):
    x = int(h)
    if (x > 0x7FFF): x-= 0x10000
    return x
def hex_to_i32(h):
    x = int(h)
    if (x > 0x7FFFFFFF): x-= 0x100000000
    return x
def hex_to_byte(h):
    x = int(h)
    if (x > 0x7F): x-= 0x100
    return x
def uint_to_i32(u):
    if (u > 0x7FFFFFFF): u-= 0x100000000
    return u

def bytes_to_string(byte_array):
    form = 'B' * len(byte_array)
    return struct.pack(form, *byte_array)

def macAddr_to_string(addr):
    byte_array = [int(b, 16) for b in addr.split(':')]
    return bytes_to_string(byte_array)

def ipv4Addr_to_i32(addr):
    byte_array = [int(b) for b in addr.split('.')]
    res = 0
    for b in byte_array: res = res * 256 + b
    return uint_to_i32(res)