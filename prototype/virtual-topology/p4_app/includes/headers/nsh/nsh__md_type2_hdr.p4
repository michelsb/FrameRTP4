header nsh_md_type2_t {
    bit<16> mdclass;
    bit<8> type;
    bit<1> u;
    bit<7> length;
    varbit<320> vlmetadata;
}