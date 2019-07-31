import os
import definitions
from db import db_manager
from utils.format import get_p4table_p4name
from utils.validate import validate_rule
from utils.config import get_controller_servers
from drivers.controller_client import RTP4ClientController
from smart_detector.decision_making import DecisionMakingModule
from rtp4rules.rtp4rules_manager import generate_wildcarded_rtp4rules

import threading

class CoreEngine:
    def __init__(self):
        # self.rtp4table_ids = []
        self.rtp4table_classes = {}
        # Create DB Connection
        db_file = os.path.join(definitions.BUILD_DIR, definitions.DB_NAME)
        self.dbms = db_manager.DBManager(db_manager.SQLITE, dbname=db_file)
        # Generate runtime classes
        self.generate_rtp4table_classes()

        # TODO: add controller_client connection
        self.client_driver = RTP4ClientController()
        self.client_driver.startClientController(get_controller_servers())

        self.decision_making = DecisionMakingModule(self)
        self.decision_making.start_decision_making()

        self.generate_wildcarded_rtp4rules()

    # Generate a model for each Real Time P4Table
    def generate_rtp4table_classes(self):
        self.dbms.create_session()
        list_rtp4table = self.dbms.list_rtp4tables()
        for rtp4table in list_rtp4table:
            p4name = get_p4table_p4name(rtp4table.prefix, rtp4table.name)
            list_key = self.dbms.list_keys_per_table(rtp4table.id)
            fields = []
            for key in list_key:
                fields.append(key.name)
            # self. rtp4table_ids.append(rtp4table.id)
            self.rtp4table_classes[rtp4table.id] = {}
            self.rtp4table_classes[rtp4table.id]["cls"] = self.dbms.create_rtp4table_dbmodel(p4name, fields)
            self.rtp4table_classes[rtp4table.id]["new_rules"] = []
            self.rtp4table_classes[rtp4table.id]["wildcard_rules"] = []
        self.dbms.close_session()

    def list_pipelines(self):
        self.dbms.create_session()
        result = [pipeline.json_dumps() for pipeline in self.dbms.list_pipelines()]
        self.dbms.close_session()
        return result

    def list_p4tables(self):
        self.dbms.create_session()
        result = [p4table.json_dumps() for p4table in self.dbms.list_p4tables()]
        self.dbms.close_session()
        return result

    def get_p4table(self, table_id):
        self.dbms.create_session()
        result = [p4table.json_dumps() for p4table in self.dbms.list_p4tables(table_id)][0]
        result["keys"] = [key.json_dumps() for key in self.dbms.list_keys_per_table(table_id)]
        result["actions"] = [action.json_dumps() for action in self.dbms.list_actions_per_table(table_id)]
        # for index in range(0,len(result["actions"])):
        #    result["actions"][index]["runtime_data"] = json.dumps(result["actions"][index]["runtime_data"])
        self.dbms.close_session()
        return result

    def list_counters(self):
        self.dbms.create_session()
        result = [counter.json_dumps() for counter in self.dbms.list_counters()]
        self.dbms.close_session()
        return result

    def generate_report(self):
        self.dbms.create_session()
        report = self.dbms.generate_report()
        self.dbms.close_session()
        return report

    def list_rtp4table_dbrules(self, table_id):
        class_model = self.rtp4table_classes[table_id]["cls"]
        self.dbms.create_session()
        db_rules = self.dbms.list_rules_per_rtp4table(class_model)
        self.dbms.close_session()
        result = []
        for db_rule in db_rules:
            result.append(db_rule.json_dumps())
        return result

    def list_p4table_rules(self, table_id):
        p4table = self.get_p4table(table_id)
        result = {}
        if p4table["id"] in self.rtp4table_classes.keys():
            result["table_type"] = "realtime"
            result["db_rules"] = self.list_rtp4table_dbrules(table_id)
        else:
            result["table_type"] = "non-realtime"
        p4table_name = get_p4table_p4name(p4table["prefix"], p4table["name"])
        result["p4_rules"] = self.client_driver.listTableRules(p4table_name)
        return result

    def add_rtp4table_dbrule(self, p4table, new_rule):
        row_entry = self.dbms.create_rtp4table_instance(self.rtp4table_classes[p4table["id"]]["cls"], new_rule)
        self.dbms.insert_rows([row_entry])

    def add_p4table_rule(self, p4table, new_rule):
        # Adding New Rule
        p4table_name = get_p4table_p4name(p4table["prefix"], p4table["name"])
        response = self.client_driver.addTableRule(p4table_name, new_rule)
        if not response:
            return response, "ERROR! The rule was not created in some tables."
        message = "Table %s was updated!" % p4table_name
        return True, message

    def add_rule(self, p4table_id, new_rule):
        p4table = self.get_p4table(p4table_id)

        # Validation Process
        response, message = validate_rule(new_rule, p4table)
        if not response:
           return response, message

        # Adding New Rule
        response, message = self.add_p4table_rule(p4table, new_rule)
        if not response:
            return response, message

        if p4table["id"] in self.rtp4table_classes.keys():
            self.add_rtp4table_dbrule(p4table, new_rule)
            self.rtp4table_classes[p4table["id"]]["new_rules"].append(new_rule)

        return True, "OK!"

    def delete_p4table_rule(self, p4table, rule):
        p4table_name = get_p4table_p4name(p4table["prefix"], p4table["name"])
        response = self.client_driver.deleteTableRule(p4table_name, rule)
        if not response:
            return response, "ERROR! Found problems while removing rules from table: " + p4table_name
        message = "All rules in table %s were deleted!" % p4table_name
        return True, message

    def delete_rtp4table_dbrule(self, p4table, rule):
        instance = self.dbms.create_rtp4table_instance(self.rtp4table_classes[p4table["id"]]["cls"], rule)
        self.dbms.create_session()
        row_entry = self.dbms.get_rule_per_rtp4table(self.rtp4table_classes[p4table["id"]]["cls"],instance)
        self.dbms.close_session()
        self.dbms.delete_rows([row_entry])

    def delete_rule(self, p4table_id, rule):
        p4table = self.get_p4table(p4table_id)

        # Validation Process
        response, message = validate_rule(rule, p4table)
        if not response:
            return response, message

        # Deleting Rule
        response, message = self.delete_p4table_rule(p4table, rule)
        if not response:
            return response, message

        if p4table["id"] in self.rtp4table_classes.keys():
            self.delete_rtp4table_dbrule(p4table, rule)

        return True, "OK!"

    def generate_wildcarded_rtp4rules(self):
        for rtp4table_id in self.rtp4table_classes.keys():
            if len(self.rtp4table_classes[rtp4table_id]["new_rules"]) >= definitions.WILDCARDS_GENERATION_THRESHOLD:
                rtp4table = self.get_p4table(rtp4table_id)
                dbrules = self.list_rtp4table_dbrules(rtp4table_id)
                new_wildcarded_rules = generate_wildcarded_rtp4rules(dbrules)
                for new_rule in self.rtp4table_classes[rtp4table_id]["new_rules"]:
                    response, message = self.delete_p4table_rule(rtp4table, new_rule)
                    if not response:
                        raise Exception(message)
                self.rtp4table_classes[rtp4table_id]["new_rules"] = []
                for old_wildcarded_rule in self.rtp4table_classes[rtp4table_id]["wildcard_rules"]:
                    response, message = self.delete_p4table_rule(rtp4table, old_wildcarded_rule)
                    if not response:
                        raise Exception(message)
                self.rtp4table_classes[rtp4table_id]["wildcard_rules"] = new_wildcarded_rules
                for new_wildcarded_rule in new_wildcarded_rules:
                    response, message = self.add_p4table_rule(rtp4table, new_wildcarded_rule)
                    if not response:
                        raise Exception(message)
        t = threading.Timer(definitions.WILDCARDS_GENERATION_TIMEOUT, self.generate_wildcarded_rtp4rules)
        t.daemon = True
        t.start()



