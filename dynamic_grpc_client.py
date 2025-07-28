import importlib
import sys
import os
from grpc_tools import protoc
from google.protobuf import descriptor_pb2
import subprocess
import grpc
import time


def print_services_from_proto(proto_path):
    desc_path = "tmp_descriptor.pb"
    subprocess.run(
        [
            "protoc",
            f"--proto_path={os.path.dirname(proto_path)}",
            f"--descriptor_set_out={desc_path}",
            "--include_imports",
            os.path.basename(proto_path),
        ],
        check=True,
    )

    with open(desc_path, "rb") as f:
        data = f.read()

    file_set = descriptor_pb2.FileDescriptorSet()
    file_set.ParseFromString(data)

    for file_desc in file_set.file:
        print(f"Proto file: {file_desc.name}")
        for service in file_desc.service:
            print(f" Service: {service.name}")
            for method in service.method:
                print(f"  RPC: {method.name}")
                print(f"    Input: {method.input_type}")
                print(f"    Output: {method.output_type}")

    os.remove(desc_path)


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
    print_services_from_proto(proto_file)
    svc = "Greeter"
    rpc = "SayHello"
    val = "Hello from dynamic client"
    print(call_rpc(proto_file, svc, rpc, val))
