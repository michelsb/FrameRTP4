from exceptions import UIn_Error

def convert_bin_to_ip(bin):
    first_octet = int(bin[0:8], 2)
    second_octet = int(bin[8:16], 2)
    third_octet = int(bin[16:24], 2)
    fourth_octet = int(bin[24:32], 2)

    return "%d.%d.%d.%d" % (first_octet, second_octet, third_octet, fourth_octet)

# thrift does not support unsigned integers
def hex_to_i16(h):
    x = int(h, 0)
    if (x > 0xFFFF):
        raise UIn_Error("Integer cannot fit within 16 bits")
    if (x > 0x7FFF): x-= 0x10000
    return x
def i16_to_hex(h):
    x = int(h)
    if (x & 0x8000): x+= 0x10000
    return x
def hex_to_i32(h):
    x = int(h, 0)
    if (x > 0xFFFFFFFF):
        raise UIn_Error("Integer cannot fit within 32 bits")
    if (x > 0x7FFFFFFF): x-= 0x100000000
    return x
def i32_to_hex(h):
    x = int(h)
    if (x & 0x80000000): x+= 0x100000000
    return x


