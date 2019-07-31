import os, sys, json, subprocess, re, argparse
import time
import definitions
from utils.config import get_rt_tables
from utils.format import format_p4table_name_entry, get_rtp4table_dbname, get_rtp4table_dbkeyname
from db import db_manager
from db.base_models import P4Table, Counter, Pipeline, Action, Key

class BuildRTP4App():
    def logger(self, *items):
        if not self.quiet:
            print(' '.join(items))

    def __init__(self, log_dir, build_dir, rtp4app_json_file, quiet=False):
        self.quiet = quiet

        exists = os.path.isfile(rtp4app_json_file)
        if not exists:
            raise Exception(" File '%s' not exists! Program Aborted! "
                            "Compiled files were not generated!" % rtp4app_json_file)
        with open(rtp4app_json_file, 'r') as f:
            self.rtp4app_json = json.load(f)

        self.build_dir = build_dir

        # Ensure all the needed directories exist and are directories
        for dir_name in [log_dir]:
            if not os.path.isdir(dir_name):
                if os.path.exists(dir_name):
                    raise Exception("'%s' exists and is not a directory!" % dir_name)
                os.mkdir(dir_name)
        self.log_dir = log_dir

        # Create DB Connection
        db_file = os.path.join(definitions.BUILD_DIR, definitions.DB_NAME)
        self.dbms = db_manager.DBManager(db_manager.SQLITE, dbname=db_file)

    def generate_rtp4app_files(self):

        list_rows = []
        rt_table_entries = []
        rt_tables = get_rt_tables()

        headers_mapper = {}
        headers_type_mapper = {}
        for header in self.rtp4app_json["headers"]:
            headers_mapper[header["name"]] = header["header_type"]
        for header_type in self.rtp4app_json["header_types"]:
            headers_type_mapper[header_type["name"]] = {}
            for field in header_type["fields"]:
                headers_type_mapper[header_type["name"]][field[0]] = field[1]

        key_count = 0
        for pipeline in self.rtp4app_json["pipelines"]:
            pipeline_entry = Pipeline(id=pipeline["id"], name=pipeline["name"])
            list_rows.append(pipeline_entry)
            for table in pipeline["tables"]:
                prefix_name, main_name = format_p4table_name_entry(table["name"])
                if main_name in rt_tables:
                    is_real_time = True
                    rt_table_entry = {"name": table["name"], "fields":[]}
                else:
                    is_real_time = False
                table_entry = P4Table(id=table["id"], prefix=prefix_name, name=main_name, max_size=table["max_size"],
                                    is_real_time=is_real_time, pipeline_id=pipeline_entry.id)
                list_rows.append(table_entry)
                for key in table["key"]:
                    size = 0
                    header_name = key["target"][0]
                    if header_name in headers_mapper.keys():
                        header_type = headers_mapper[header_name]
                        field_name = key["target"][1]
                        if field_name in headers_type_mapper[header_type].keys():
                            size = headers_type_mapper[header_type][field_name]
                    key_entry = Key(id=key_count, name=key["name"], match_type=key["match_type"], size=size,
                                    table_id=table_entry.id)
                    key_count += 1
                    list_rows.append(key_entry)
                    if is_real_time:
                        if key["match_type"] != "ternary":
                            raise Exception(" '%s' field  in table '%s' is not ternary! "
                                            "All match fields in a Real Time Table must be ternary! Program Aborted!" % (str(key["name"]),str(table["name"])))
                        rt_table_entry["fields"].append(key["name"])
                if is_real_time:
                    rt_table_entries.append(rt_table_entry)
                for action in self.rtp4app_json["actions"]:
                    if action["id"] in table["action_ids"]:
                        action_entry = Action(id=action["id"], name=action["name"],
                                              runtime_data=str(action["runtime_data"]), table_id=table_entry.id)
                        list_rows.append(action_entry)
        for counter in self.rtp4app_json["counter_arrays"]:
            counter_entry = Counter(id=counter["id"], name=counter["name"], size=counter["size"],
                                    is_direct=counter["is_direct"])
            list_rows.append(counter_entry)

        self.logger("Creating Database...")
        for rt_table_entry in rt_table_entries:
            self.dbms.create_rtp4table_dbmodel(rt_table_entry["name"], rt_table_entry["fields"])
        self.dbms.create_db_tables()

        time.sleep(3)

        self.logger("Populating Database...")
        self.dbms.insert_rows(list_rows)


def get_args():
    default_build = definitions.BUILD_DIR
    default_logs = definitions.LOG_DIR
    default_json = os.path.join(definitions.BUILD_DIR, definitions.JSON_NAME)
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--quiet', help='Suppress log messages.',
                            action='store_true', required=False, default=False)
    parser.add_argument('-b', '--build-dir', type=str, required=False, default=default_build)
    parser.add_argument('-l', '--log-dir', type=str, required=False, default=default_logs)
    parser.add_argument('-j', '--rtp4app-json', type=str, required=False, default=default_json)

    return parser.parse_args()

# run the program
if __name__ == '__main__':
    args = get_args()
    build = BuildRTP4App(args.log_dir, args.build_dir, args.rtp4app_json, args.quiet)
    build.generate_rtp4app_files()

