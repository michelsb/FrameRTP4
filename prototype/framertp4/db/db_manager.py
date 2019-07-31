from sqlalchemy import create_engine, Column, Table, Integer, String
from sqlalchemy.orm import sessionmaker

from db.base_models import Base, P4Table, Counter, Pipeline, Action, Key, create_rtp4table_dbmodel, create_rtp4table_instance, get_instance_filters

# Global Variables
SQLITE = 'sqlite'

class DBManager:
    # http://docs.sqlalchemy.org/en/latest/core/engines.html
    DB_ENGINE = {
        SQLITE: 'sqlite:///{DB}'
    }

    # Main DB Connection Ref Obj
    db_engine = None
    db_session = None

    def __init__(self, dbtype, username='', password='', dbname=''):
        dbtype = dbtype.lower()
        if dbtype in self.DB_ENGINE.keys():
            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
            self.db_engine = create_engine(engine_url)
            print(self.db_engine)
        else:
            print("DBType is not found in DB_ENGINE")

    def create_db_tables(self):
        try:
            Base.metadata.create_all(self.db_engine)
            print("Tables created!")
        except Exception as e:
            print("Error occurred during Table creation!")
            print(e)

    def create_session(self):
        Base.metadata.bind = self.db_engine
        DBSession = sessionmaker(bind=self.db_engine)
        # A DBSession() instance establishes all conversations with the database
        # and represents a "staging zone" for all the objects loaded into the
        # database session object. Any change made against the objects in the
        # session won't be persisted into the database until you call
        # session.commit(). If you're not happy about the changes, you can
        # revert all of them back to the last commit by calling
        # session.rollback()
        self.db_session = DBSession()

    def close_session(self):
        self.db_session.close()

    def insert_rows(self, list_rows):
        self.create_session()
        for row_entry in list_rows:
            self.db_session.add(row_entry)
        self.db_session.commit()
        self.close_session()

    def delete_rows(self, list_rows):
        self.create_session()
        for row_entry in list_rows:
            self.db_session.delete(row_entry)
        self.db_session.commit()
        self.close_session()

    def list_rtp4tables(self):
        #self.create_session()
        list_rtp4table = self.db_session.query(P4Table).filter(P4Table.is_real_time == True).all()
        #self.close_session()
        return list_rtp4table

    def list_pipelines(self):
        #self.create_session()
        list_pipeline = self.db_session.query(Pipeline).all()
        #self.close_session()
        return list_pipeline

    def list_p4tables(self, table_id=None):
        if table_id is None:
            list_table = self.db_session.query(P4Table).all()
        else:
            list_table = self.db_session.query(P4Table).filter(P4Table.id == table_id).all()
        return list_table

    def list_actions(self):
        list_action = self.db_session.query(Action).all()
        return list_action

    def list_actions_per_table(self, table_id):
        list_action = self.db_session.query(Action).filter(Action.table_id == table_id).all()
        return list_action

    def list_keys(self):
        list_key = self.db_session.query(Key).all()
        return list_key

    def list_keys_per_table(self, table_id):
        list_key = self.db_session.query(Key).filter(Key.table_id == table_id).all()
        return list_key

    def list_counters(self):
        #self.create_session()
        list_counter = self.db_session.query(Counter).all()
        #self.close_session()
        return list_counter

    def list_rules_per_rtp4table(self, cls):
        list_rules = self.db_session.query(cls).all()
        return list_rules

    def get_rule_per_rtp4table(self, cls, instance):
        filters = get_instance_filters(cls,instance)
        rule = self.db_session.query(cls).filter(*filters).first()
        print(rule.json_dumps())
        return rule

    def generate_report(self):
        #self.create_session()
        report = {}
        pipelines = self.list_pipelines()
        for pipeline in pipelines:
            report[pipeline.name] = {}
            tables = self.db_session.query(P4Table).filter(P4Table.pipeline_id == pipeline.id).all()
            for table in tables:
                report[pipeline.name][table.name] = {"keys":[],"actions":[]}
                keys = self.db_session.query(Key).filter(Key.table_id == table.id).all()
                actions = self.db_session.query(Action).filter(Action.table_id == table.id).all()
                for key in keys:
                    report[pipeline.name][table.name]["keys"].append(key.name)
                for action in actions:
                    report[pipeline.name][table.name]["actions"].append(action.name)
        #self.close_session()
        return report

    def create_rtp4table_dbmodel(self, name, match_fields):
        class_model = create_rtp4table_dbmodel(name, match_fields)
        return class_model

    def create_rtp4table_instance(self, cls, new_rule):
        rtp4table_instance = create_rtp4table_instance(cls, new_rule)
        return rtp4table_instance

    # Insert, Update, Delete
    def execute_query(self, query=''):
        if query == '': return
        print (query)
        with self.db_engine.connect() as connection:
            try:
                connection.execute(query)
            except Exception as e:
                print(e)



