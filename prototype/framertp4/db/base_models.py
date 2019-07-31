from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import copy
from utils.format import get_rtp4table_dbname, get_rtp4table_dbkeyname

Base = declarative_base()

class Pipeline(Base):
    __tablename__ = 'pipeline'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    def json_dumps(self):
        json_format = {"id":self.id, "name":self.name}
        return json_format

class P4Table(Base):
    __tablename__ = 'table'
    id = Column(Integer, primary_key=True)
    prefix = Column(String(250))
    name = Column(String(250), nullable=False)
    max_size = Column(Integer, nullable=False)
    is_real_time = Column(Boolean, default=False, nullable=False)
    pipeline_id = Column(Integer, ForeignKey('pipeline.id'))
    pipeline = relationship(Pipeline)

    def json_dumps(self):
        json_format = {"id":self.id, "prefix":self.prefix, "name":self.name, "max_size":self.max_size, "is_real_time": self.is_real_time, "pipeline_id": self.pipeline_id}
        return json_format

class Counter(Base):
    __tablename__ = 'counter'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    size = Column(Integer, nullable=False)
    is_direct = Column(Boolean, default=False, nullable=False)

    def json_dumps(self):
        json_format = {"id":self.id, "name":self.name, "size":self.size, "is_direct": self.is_direct}
        return json_format

class Action(Base):
    __tablename__ = 'action'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    runtime_data = Column(String(250))
    table_id = Column(Integer, ForeignKey('table.id'))
    table = relationship(P4Table)

    def json_dumps(self):
        json_format = {"id":self.id, "name":self.name, "runtime_data":eval(self.runtime_data), "table_id": self.table_id}
        return json_format

class Key(Base):
    __tablename__ = 'key'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    match_type = Column(String(250), nullable=False)
    size = Column(Integer, nullable=False)
    table_id = Column(Integer, ForeignKey('table.id'))
    table = relationship(P4Table)

    def json_dumps(self):
        json_format = {"id":self.id, "name":self.name, "match_type":self.match_type, "size": self.size,"table_id": self.table_id}
        return json_format

template_rtp4table_entry = {"id":0,"match_fields":{},"action_name":"","action_params":{},"priority":0}

def json_dumps(self):
    attributes = vars(self)
    json_format = copy.deepcopy(template_rtp4table_entry)
    json_format["id"] = attributes["id"]
    for match_field in self.list_match_fields:
        json_format["match_fields"][match_field] = eval(attributes[get_rtp4table_dbkeyname(match_field)])
    json_format["action_name"] = attributes["action_name"]
    json_format["action_params"] = eval(attributes["action_params"])
    json_format["priority"] = attributes["priority"]
    #json_format = {}
    #for attr in items:
    #    if not attr.startswith('_'):
    #        json_format[attr] = items[attr]
    return json_format



def create_rtp4table_dbmodel(name, match_fields):
    rtp4table_dbname = get_rtp4table_dbname(name)
    attributes = {}
    attributes["__tablename__"] = rtp4table_dbname
    attributes["__table_args__"] = {"sqlite_autoincrement": True}
    attributes["id"] = Column(Integer, primary_key=True)
    for match_field in match_fields:
        match_field = get_rtp4table_dbkeyname(match_field)
        attributes[match_field] = Column(String(250))
    attributes["action_name"] = Column(String(250), nullable=False)
    attributes["action_params"] = Column(String(250), nullable=False)
    attributes["priority"] = Column(Integer, nullable=False)
    attributes["list_match_fields"] = match_fields
    attributes["json_dumps"] = json_dumps
    class_model = type(rtp4table_dbname,(Base,),attributes)
    return class_model

def create_rtp4table_instance(cls, new_rule):
    rtp4table_instance = cls()
    for match_field in new_rule["match_fields"].keys():
        db_match_field = get_rtp4table_dbkeyname(match_field)
        setattr(rtp4table_instance,db_match_field,str(new_rule["match_fields"][match_field]))
    setattr(rtp4table_instance, "action_name", new_rule["action_name"])
    setattr(rtp4table_instance, "action_params", str(new_rule["action_params"]))
    setattr(rtp4table_instance, "priority", new_rule["priority"])
    return rtp4table_instance

def get_instance_filters(cls, instance):
    filters = []
    for match_field in getattr(cls, "list_match_fields"):
        db_match_field = get_rtp4table_dbkeyname(match_field)
        filters.append(getattr(cls,db_match_field).like(getattr(instance,db_match_field)))
    filters.append(getattr(cls, "action_name").like(getattr(instance, "action_name")))
    filters.append(getattr(cls, "action_params").like(getattr(instance, "action_params")))
    filters.append(getattr(cls, "priority").like(getattr(instance, "priority")))
    return filters
