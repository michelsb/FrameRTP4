import sys
import json
from collections import Counter
from exceptions import *

TABLES = {}
ACTION_PROFS = {}
ACTIONS = {}
METER_ARRAYS = {}
COUNTER_ARRAYS = {}
REGISTER_ARRAYS = {}
CUSTOM_CRC_CALCS = {}

# maps (object type, unique suffix) to object
SUFFIX_LOOKUP_MAP = {}

def enum(type_name, *sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())

    @staticmethod
    def to_str(x):
        return reverse[x]
    enums['to_str'] = to_str

    @staticmethod
    def from_str(x):
        return enums[x]

    enums['from_str'] = from_str
    return type(type_name, (), enums)

#PreType = enum('PreType', 'None', 'SimplePre', 'SimplePreLAG')
MeterType = enum('MeterType', 'packets', 'bytes')
TableType = enum('TableType', 'simple', 'indirect', 'indirect_ws')
ResType = enum('ResType', 'table', 'action_prof', 'action', 'meter_array',
'counter_array', 'register_array')

class MatchType:
    EXACT = 0
    LPM = 1
    TERNARY = 2
    VALID = 3
    RANGE = 4

    @staticmethod
    def to_str(x):
        return {0: "exact", 1: "lpm", 2: "ternary", 3: "valid", 4: "range"}[x]

    @staticmethod
    def from_str(x):
        return {"exact": 0, "lpm": 1, "ternary": 2, "valid": 3, "range": 4}[x]

class Table:
    def __init__(self, name, id_):
        self.name = name
        self.id_ = id_
        self.match_type_ = None
        self.actions = {}
        self.key = []
        self.default_action = None
        self.type_ = None
        self.support_timeout = False
        self.action_prof = None

        TABLES[name] = self

    def num_key_fields(self):
        return len(self.key)

    def key_str(self):
        return ",\t".join([name + "(" + MatchType.to_str(t) + ", " + str(bw) + ")" for name, t, bw in self.key])

    def table_str(self):
        ap_str = "implementation={}".format(
            "None" if not self.action_prof else self.action_prof.name)
        return "{0:30} [{1}, mk={2}]".format(self.name, ap_str, self.key_str())

    def get_action(self, action_name):
        key = ResType.action, action_name
        action = SUFFIX_LOOKUP_MAP.get(key, None)
        if action is None or action.name not in self.actions:
            return None
        return action

class ActionProf:
    def __init__(self, name, id_):
        self.name = name
        self.id_ = id_
        self.with_selection = False
        self.actions = {}
        self.ref_cnt = 0

        ACTION_PROFS[name] = self

    def action_prof_str(self):
        return "{0:30} [{1}]".format(self.name, self.with_selection)

    def get_action(self, action_name):
        key = ResType.action, action_name
        action = SUFFIX_LOOKUP_MAP.get(key, None)
        if action is None or action.name not in self.actions:
            return None
        return action

class Action:
    def __init__(self, name, id_):
        self.name = name
        self.id_ = id_
        self.runtime_data = []

        ACTIONS[name] = self

    def num_params(self):
        return len(self.runtime_data)

    def runtime_data_str(self):
        return ",\t".join([name + "(" + str(bw) + ")" for name, bw in self.runtime_data])

    def action_str(self):
        return "{0:30} [{1}]".format(self.name, self.runtime_data_str())

class MeterArray:
    def __init__(self, name, id_):
        self.name = name
        self.id_ = id_
        self.type_ = None
        self.is_direct = None
        self.size = None
        self.binding = None
        self.rate_count = None

        METER_ARRAYS[name] = self

    def meter_str(self):
        return "{0:30} [{1}, {2}]".format(self.name, self.size,
                                          MeterType.to_str(self.type_))

class CounterArray:
    def __init__(self, name, id_):
        self.name = name
        self.id_ = id_
        self.is_direct = None
        self.size = None
        self.binding = None

        COUNTER_ARRAYS[name] = self

    def counter_str(self):
        return "{0:30} [{1}]".format(self.name, self.size)

class RegisterArray:
    def __init__(self, name, id_):
        self.name = name
        self.id_ = id_
        self.width = None
        self.size = None

        REGISTER_ARRAYS[name] = self

    def register_str(self):
        return "{0:30} [{1}]".format(self.name, self.size)

def reset_config():
    TABLES.clear()
    ACTION_PROFS.clear()
    ACTIONS.clear()
    METER_ARRAYS.clear()
    COUNTER_ARRAYS.clear()
    REGISTER_ARRAYS.clear()
    CUSTOM_CRC_CALCS.clear()
    SUFFIX_LOOKUP_MAP.clear()

def load_json_str(json_str):
    def get_header_type(header_name, j_headers):
        for h in j_headers:
            if h["name"] == header_name:
                return h["header_type"]
        assert(0)

    def get_field_bitwidth(header_type, field_name, j_header_types):
        for h in j_header_types:
            if h["name"] != header_type: continue
            for t in h["fields"]:
                # t can have a third element (field signedness)
                f, bw = t[0], t[1]
                if f == field_name:
                    return bw
        assert(0)

    reset_config()
    json_ = json.loads(json_str)

    def get_json_key(key):
        return json_.get(key, [])

    for j_action in get_json_key("actions"):
        action = Action(j_action["name"], j_action["id"])
        for j_param in j_action["runtime_data"]:
            action.runtime_data += [(j_param["name"], j_param["bitwidth"])]

    for j_pipeline in get_json_key("pipelines"):
        if "action_profiles" in j_pipeline:  # new JSON format
            for j_aprof in j_pipeline["action_profiles"]:
                action_prof = ActionProf(j_aprof["name"], j_aprof["id"])
                action_prof.with_selection = "selector" in j_aprof

        for j_table in j_pipeline["tables"]:
            table = Table(j_table["name"], j_table["id"])
            table.match_type = MatchType.from_str(j_table["match_type"])
            table.type_ = TableType.from_str(j_table["type"])
            table.support_timeout = j_table["support_timeout"]
            for action in j_table["actions"]:
                table.actions[action] = ACTIONS[action]

            if table.type_ in {TableType.indirect, TableType.indirect_ws}:
                if "action_profile" in j_table:
                    action_prof = ACTION_PROFS[j_table["action_profile"]]
                else:  # for backward compatibility
                    assert("act_prof_name" in j_table)
                    action_prof = ActionProf(j_table["act_prof_name"],
                                             table.id_)
                    action_prof.with_selection = "selector" in j_table
                action_prof.actions.update(table.actions)
                action_prof.ref_cnt += 1
                table.action_prof = action_prof

            for j_key in j_table["key"]:
                target = j_key["target"]
                match_type = MatchType.from_str(j_key["match_type"])
                if match_type == MatchType.VALID:
                    field_name = target + "_valid"
                    bitwidth = 1
                elif target[1] == "$valid$":
                    field_name = target[0] + "_valid"
                    bitwidth = 1
                else:
                    field_name = ".".join(target)
                    header_type = get_header_type(target[0],
                                                  json_["headers"])
                    bitwidth = get_field_bitwidth(header_type, target[1],
                                                  json_["header_types"])
                table.key += [(field_name, match_type, bitwidth)]

    for j_meter in get_json_key("meter_arrays"):
        meter_array = MeterArray(j_meter["name"], j_meter["id"])
        if "is_direct" in j_meter and j_meter["is_direct"]:
            meter_array.is_direct = True
            meter_array.binding = j_meter["binding"]
        else:
            meter_array.is_direct = False
            meter_array.size = j_meter["size"]
        meter_array.type_ = MeterType.from_str(j_meter["type"])
        meter_array.rate_count = j_meter["rate_count"]

    for j_counter in get_json_key("counter_arrays"):
        counter_array = CounterArray(j_counter["name"], j_counter["id"])
        counter_array.is_direct = j_counter["is_direct"]
        if counter_array.is_direct:
            counter_array.binding = j_counter["binding"]
        else:
            counter_array.size = j_counter["size"]

    for j_register in get_json_key("register_arrays"):
        register_array = RegisterArray(j_register["name"], j_register["id"])
        register_array.size = j_register["size"]
        register_array.width = j_register["bitwidth"]

    for j_calc in get_json_key("calculations"):
        calc_name = j_calc["name"]
        if j_calc["algo"] == "crc16_custom":
            CUSTOM_CRC_CALCS[calc_name] = 16
        elif j_calc["algo"] == "crc32_custom":
            CUSTOM_CRC_CALCS[calc_name] = 32

    # Builds a dictionary mapping (object type, unique suffix) to the object
    # (Table, Action, etc...). In P4_16 the object name is the fully-qualified
    # name, which can be quite long, which is why we accept unique suffixes as
    # valid identifiers.
    # Auto-complete does not support suffixes, only the fully-qualified names,
    # but that can be changed in the future if needed.
    suffix_count = Counter()
    for res_type, res_dict in [
            (ResType.table, TABLES), (ResType.action_prof, ACTION_PROFS),
            (ResType.action, ACTIONS), (ResType.meter_array, METER_ARRAYS),
            (ResType.counter_array, COUNTER_ARRAYS),
            (ResType.register_array, REGISTER_ARRAYS)]:
        for name, res in res_dict.items():
            suffix = None
            for s in reversed(name.split('.')):
                suffix = s if suffix is None else s + '.' + suffix
                key = (res_type, suffix)
                SUFFIX_LOOKUP_MAP[key] = res
                suffix_count[key] += 1
    for key, c in suffix_count.items():
        if c > 1:
            del SUFFIX_LOOKUP_MAP[key]

def get_res(type_name, name, res_type):
    key = res_type, name
    if key not in SUFFIX_LOOKUP_MAP:
        raise UIn_ResourceError(type_name, name)
    return SUFFIX_LOOKUP_MAP[key]

class RegisterManager():

    def __init__(self, client):
        self.client = client

    def do_register_read(self, reg_name, reg_id=None):
        register_name = reg_name
        register = get_res("register", register_name,
                                ResType.register_array)
        response = []
        if reg_id is not None:
            index = reg_id
            try:
                index = int(index)
            except:
                raise UIn_Error("Bad format for index")
            value = self.client.bm_register_read(0, register.name, index)
            #response = "{}[{}]=".format(register_name, index), value
            response.append(value)
        else:
            #sys.stderr.write("register index omitted, reading entire array\n")
            entries = self.client.bm_register_read_all(0, register.name)
            #response = "{}=".format(register_name), ", ".join(
                #[str(e) for e in entries])
            response = [e for e in entries]
        return response

    def do_register_write(self, reg_name, reg_index, reg_value):
        register_name = reg_name
        register = get_res("register", register_name,
                                ResType.register_array)
        index = reg_index
        try:
            index = int(index)
        except:
            raise UIn_Error("Bad format for index")
        value = reg_value
        try:
            value = int(value)
        except:
            raise UIn_Error("Bad format for value, must be an integer")
        self.client.bm_register_write(0, register.name, index, value)

    def do_register_reset(self, reg_name):
        register_name = reg_name
        register = get_res("register", register_name,
                                ResType.register_array)
        self.client.bm_register_reset(0, register.name)

class CounterManager():

    def __init__(self, client):
        self.client = client

    def do_counter_read_all(self, counter_name):
        counter = get_res("counter", counter_name, ResType.counter_array)
        response = []
        for index in range(0,counter.size):
            response.append(self.client.bm_counter_read(0, counter.name, index))
        return response


    def do_counter_read(self, counter_name, counter_id=None):
        counter = get_res("counter", counter_name, ResType.counter_array)
        response = []
        if counter_id is not None:
            index=counter_id
            try:
                index = int(index)
            except:
                raise UIn_Error("Bad format for index")
            if counter.is_direct:
                table_name = counter.binding
                print "this is the direct counter for table", table_name
                # index = index & 0xffffffff
                value = self.client.bm_mt_read_counter(0, table_name, index)
            else:
                value = self.client.bm_counter_read(0, counter.name, index)
            response.append(value)
        # else:
        #     if counter.is_direct:
        #         table_name = counter.binding
        #         print "this is the direct counter for table", table_name
        #         # index = index & 0xffffffff
        #         entries = self.client.bm_mt_read_counter(0, table_name)
        #     else:
        #         entries = self.client.bm_counter_read(0, counter.name)
        #     response = [e for e in entries]

        return response

    def do_counter_reset(self, counter_name):
        counter = get_res("counter", counter_name, ResType.counter_array)
        if counter.is_direct:
            table_name = counter.binding
            print "this is the direct counter for table", table_name
            self.client.bm_mt_reset_counters(0, table_name)
        else:
            self.client.bm_counter_reset_all(0, counter.name)