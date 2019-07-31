header nsh_base_t {
    bit<2> version;
    bit<1> o;
    bit<1> u1;
    bit<6> ttl;
    bit<6> length;
    bit<1> u2;
    bit<1> u3;
    bit<1> u4;
    bit<1> u5;
    bit<4> mdtype;
    bit<8> protocol;
}