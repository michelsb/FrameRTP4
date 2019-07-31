from configparser import SafeConfigParser
import definitions

parser = SafeConfigParser()
parser.read(definitions.CONFIG_FILE)

def get_rt_tables():
    return str(parser.get("TABLES", "REAL_TIME_TABLES")).replace(" ", "").split(",")

def get_controller_servers():
    return str(parser.get("CONTROLLERS", "LIST_SERVERS")).replace(" ", "").split(",")