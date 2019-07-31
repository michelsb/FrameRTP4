import json
from flask import Flask, request

from core.core_engine import CoreEngine
from utils.response import json_response, JSON_MIME_TYPE

app = Flask(__name__)
core = CoreEngine()

@app.route('/',methods=["GET"])
def generate_report():
    content = core.generate_report()
    response = json.dumps(content)
    return json_response(response)

@app.route('/pipeline', methods=["GET"])
def list_pipelines():
    content = core.list_pipelines()
    response = json.dumps(content)
    return json_response(response)

#@app.route('/pipeline/<int:pipeline_id>')

@app.route('/p4table', methods=["GET"])
def list_p4tables():
    content = core.list_p4tables()
    response = json.dumps(content)
    return json_response(response)

@app.route('/p4table/<int:table_id>', methods=["GET"])
def list_p4tables_per_id(table_id):
    content = core.get_p4table(table_id)
    response = json.dumps(content)
    return json_response(response)

#@app.route('/action')

#@app.route('/action/<int:action_id>')

#@app.route('/key')

#@app.route('/key/<int:key_id>')

@app.route('/counter', methods=["GET"])
def list_counters():
    content = core.list_counters()
    response = json.dumps(content)
    return json_response(response)

#@app.route('/counter/<int:counter_id>')

@app.route('/p4table/<int:table_id>/rule', methods=['GET'])
def list_p4table_rules(table_id):
    content = core.list_p4table_rules(table_id)
    response = json.dumps(content)
    return json_response(response)

@app.route('/p4table/<int:table_id>/rule', methods=['PUT'])
def create_p4table_rule(table_id):
    if request.content_type != JSON_MIME_TYPE:
        error = json.dumps({'error': 'Invalid Content Type'})
        return json_response(error, 400)
    data = request.json
    response, message = core.add_rule(table_id,data)
    if response:
        return json_response(message, status=201)
    else:
        error = json.dumps({'error': message})
        return json_response(error, 400)

@app.route('/p4table/<int:table_id>/rule', methods=['DELETE'])
def delete_p4table_rule(table_id):
    if request.content_type != JSON_MIME_TYPE:
        error = json.dumps({'error': 'Invalid Content Type'})
        return json_response(error, 400)
    data = request.json
    response, message = core.delete_rule(table_id,data)
    if response:
        return json_response(message, status=201)
    else:
        error = json.dumps({'error': message})
        return json_response(error, 400)

@app.errorhandler(404)
def not_found(e):
    return '', 404

# TODO list controllers and switches
# TODO add/delete rule per controller and per switch