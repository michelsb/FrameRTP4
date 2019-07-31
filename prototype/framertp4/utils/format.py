def format_p4table_name_entry(json_name):
    full_name = json_name.split(".")
    prefix_name = ""
    if len(full_name) > 1:
        prefix_name = str(full_name[0])
        main_name = str(full_name[1])
    else:
        main_name = str(full_name[0])
    return prefix_name, main_name

def get_rtp4table_dbname(tablename):
    rtp4table_dbname = str(tablename).replace(".","_")
    return rtp4table_dbname

def get_rtp4table_dbkeyname(keyname):
    rtp4table_keyname = str(keyname).replace(".","_")
    return rtp4table_keyname

def get_p4table_p4name(prefix_name,main_name):
    if prefix_name != "":
        p4table_name = str(prefix_name)+"."+str(main_name)
    else:
        p4table_name = str(main_name)
    return p4table_name







