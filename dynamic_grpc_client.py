import importlib
import sys
import os
from grpc_tools import protoc
import grpc
import time


def compile_proto(proto_path, out_dir="."):
    proto_dir = os.path.dirname(proto_path)
    proto_file = os.path.basename(proto_path)

    protoc_args = [
        "grpc_tools.protoc",
        f"-I{proto_dir}",
        f"--python_out={out_dir}",
        f"--grpc_python_out={out_dir}",
        os.path.join(proto_dir, proto_file),
    ]

    if protoc.main(protoc_args) != 0:
        raise RuntimeError("protoc fail")


def dynamic_import(module_name, module_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def call_rpc(
    proto_path, service_name, method_name, input_value, host="localhost:50051"
):
    out_dir = "."
    compile_proto(proto_path, out_dir)

    base_name = os.path.splitext(os.path.basename(proto_path))[0]
    pb2 = dynamic_import(f"{base_name}_pb2", f"{base_name}_pb2.py")
    pb2_grpc = dynamic_import(f"{base_name}_pb2_grpc", f"{base_name}_pb2_grpc.py")

    channel = grpc.insecure_channel(host)

    stub_class = getattr(pb2_grpc, f"{service_name}Stub")
    stub = stub_class(channel)

    method = getattr(stub, method_name)
    req = pb2.StringValue(value=input_value)
    resp = method(req)
    return resp.value


if __name__ == "__main__":
    proto_file = "./proto/greeter.proto"
    svc = "Greeter"
    rpc = "SayHello"
    val = "Hello from dynamic client"

    print(call_rpc(proto_file, svc, rpc, val))
