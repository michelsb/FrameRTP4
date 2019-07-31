from Queue import Queue
from abc import abstractmethod
from datetime import datetime

import grpc
from p4 import p4runtime_pb2
from p4.tmp import p4config_pb2

from p4thrift_lib.p4thrift_manager import thrift_connect_standard, thrift_disconnect, get_json_config
from p4thrift_lib.p4app_manager import load_json_str, RegisterManager, CounterManager

MSG_LOG_MAX_LEN = 1024

# List of requisitions
reqs = []

def buildDeviceConfig(bmv2_json_file_path=None):
    "Builds the device config for BMv2"
    device_config = p4config_pb2.P4DeviceConfig()
    device_config.reassign = True
    with open(bmv2_json_file_path) as f:
        device_config.device_data = f.read()
    return device_config

class GrpcRequestLogger(grpc.UnaryUnaryClientInterceptor,
                        grpc.UnaryStreamClientInterceptor):
    """Implementation of a gRPC interceptor that logs request to a file"""

    def __init__(self, log_file):
        self.log_file = log_file
        with open(self.log_file, 'w') as f:
            # Clear content if it exists.
            f.write("")

    def log_message(self, method_name, body):
        with open(self.log_file, 'a') as f:
            ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            msg = str(body)
            f.write("\n[%s] %s\n---\n" % (ts, method_name))
            if len(msg) < MSG_LOG_MAX_LEN:
                f.write(str(body))
            else:
                f.write("Message too long (%d bytes)! Skipping log...\n" % len(msg))
            f.write('---\n')

    def intercept_unary_unary(self, continuation, client_call_details, request):
        self.log_message(client_call_details.method, request)
        return continuation(client_call_details, request)

    def intercept_unary_stream(self, continuation, client_call_details, request):
        self.log_message(client_call_details.method, request)
        return continuation(client_call_details, request)

class IterableQueue(Queue):
    _sentinel = object()

    def __iter__(self):
        return iter(self.get, self._sentinel)

    def close(self):
        self.put(self._sentinel)

class P4Switch(object):

    def __init__(self, p4_json_filepath, name=None, address='localhost', grpc_port=50051, thrift_port=9090,
                 proto_dump_file=None, device_id=0):
        self.name = name
        self.p4runtime_address = address + ":" + str(grpc_port)
        self.device_id = device_id
        self.p4info = None
        self.thrift_ip = address
        self.thrift_port = thrift_port
        self.p4_json_filepath = p4_json_filepath
        self.proto_dump_file = proto_dump_file

    def buildDeviceConfig(self, **kwargs):
        return buildDeviceConfig(**kwargs)

    # GRPC Connection

    def connect_p4runtime(self):
        self.channel = grpc.insecure_channel(self.p4runtime_address)
        if self.proto_dump_file is not None:
            interceptor = GrpcRequestLogger(self.proto_dump_file)
            self.channel = grpc.intercept_channel(self.channel, interceptor)
        self.client_stub = p4runtime_pb2.P4RuntimeStub(self.channel)
        self.requests_stream = IterableQueue()
        self.stream_msg_resp = self.client_stub.StreamChannel(iter(self.requests_stream))

        self.MasterArbitrationUpdate()

    def disconnect_p4runtime(self):
        self.requests_stream.close()
        self.stream_msg_resp.cancel()

    ## THRIFT Connection

    def load_json_config(self):
        load_json_str(get_json_config(self.standard_client, self.p4_json_filepath))

    def connect_p4thrift(self):
        self.standard_client, self.transport = thrift_connect_standard(self.thrift_ip, self.thrift_port)
        self.load_json_config()
        self.register = RegisterManager(self.standard_client)
        self.counter = CounterManager(self.standard_client)

    def disconnect_p4thrift(self):
        thrift_disconnect(self.transport)

    ## GRPC Methods

    def MasterArbitrationUpdate(self, dry_run=False, **kwargs):
        request = p4runtime_pb2.StreamMessageRequest()
        request.arbitration.device_id = self.device_id
        request.arbitration.election_id.high = 0
        request.arbitration.election_id.low = 1

        if dry_run:
            print "P4Runtime MasterArbitrationUpdate: ", request
        else:
            self.requests_stream.put(request)
            for item in self.stream_msg_resp:
                return item # just one

    def SetForwardingPipelineConfig(self, p4info, dry_run=False, **kwargs):
        device_config = self.buildDeviceConfig(**kwargs)
        request = p4runtime_pb2.SetForwardingPipelineConfigRequest()
        request.election_id.low = 1
        request.device_id = self.device_id
        config = request.config

        config.p4info.CopyFrom(p4info)
        config.p4_device_config = device_config.SerializeToString()

        request.action = p4runtime_pb2.SetForwardingPipelineConfigRequest.VERIFY_AND_COMMIT
        if dry_run:
            print "P4Runtime SetForwardingPipelineConfig:", request
        else:
            self.client_stub.SetForwardingPipelineConfig(request)

    def DeleteTableEntry(self, table_entry, dry_run=False):
        request = p4runtime_pb2.WriteRequest()
        request.device_id = self.device_id
        request.election_id.low = 1
        update = request.updates.add()
        update.type = p4runtime_pb2.Update.DELETE
        update.entity.table_entry.CopyFrom(table_entry)
        if dry_run:
            print "P4Runtime Write:", request
        else:
            self.client_stub.Write(request)

    def DeleteAllTableEntries(self, table_id, dry_run=False):
        print "DeleteTableEntry() is called, device_id=", self.device_id
        updates = []
        for req in reversed(self._reqs):
            for update in reversed(req.updates):
                if update.type == p4runtime_pb2.Update.INSERT:
                    if update.entity.table_entry.table_id == table_id:
                        updates.append(update)
        new_req = p4runtime_pb2.WriteRequest()
        new_req.device_id = self.device_id
        for update in updates:
            update.type = p4runtime_pb2.Update.DELETE
            new_req.updates.add().CopyFrom(update)
        if dry_run:
            print "P4 Runtime Write:", new_req
        else:
            self.client_stub.Write(new_req)

    def WriteTableEntry(self, table_entry, dry_run=False):
        request = p4runtime_pb2.WriteRequest()
        request.device_id = self.device_id
        request.election_id.low = 1
        update = request.updates.add()
        update.type = p4runtime_pb2.Update.INSERT
        update.entity.table_entry.CopyFrom(table_entry)
        if dry_run:
            print "P4Runtime Write:", request
        else:
            self.client_stub.Write(request)

    def WriteListTableEntry(self, list_table_entry, dry_run=False):
        request = p4runtime_pb2.WriteRequest()
        request.device_id = self.device_id
        request.election_id.low = 1
        for table_entry in list_table_entry:
            update = request.updates.add()
            update.type = p4runtime_pb2.Update.INSERT
            update.entity.table_entry.CopyFrom(table_entry)
        if dry_run:
            print "P4Runtime Write:", request
        else:
            self.client_stub.Write(request)

    def ReadTableEntries(self, table_id=None, dry_run=False):
        request = p4runtime_pb2.ReadRequest()
        request.device_id = self.device_id
        entity = request.entities.add()
        table_entry = entity.table_entry
        if table_id is not None:
            table_entry.table_id = table_id
        else:
            table_entry.table_id = 0
        if dry_run:
            print "P4Runtime Read:", request
        else:
            for response in self.client_stub.Read(request):
                yield response

    def ReadCounters(self, counter_id=None, index=None, dry_run=False):
        request = p4runtime_pb2.ReadRequest()
        request.device_id = self.device_id
        entity = request.entities.add()
        counter_entry = entity.counter_entry
        if counter_id is not None:
            counter_entry.counter_id = counter_id
        else:
            counter_entry.counter_id = 0
        if index is not None:
            counter_entry.index.index = index
        if dry_run:
            print "P4Runtime Read:", request
        else:
            for response in self.client_stub.Read(request):
                yield response

    ## THRIFT Methods

    def ReadRegister(self, register_name):
        response = self.register.do_register_read(register_name)
        return response

    def ResetRegister(self, register_name):
        self.register.do_register_reset(register_name)

    def ReadCounter(self, counter_name):
        response = self.counter.do_counter_read_all(counter_name)
        return response

    def ResetCounter(self, counter_name):
        self.counter.do_counter_reset(counter_name)