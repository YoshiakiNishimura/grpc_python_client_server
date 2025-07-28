import grpc
from concurrent import futures
import subprocess
import importlib
import sys
import os


def generate_proto(proto_path, proto_dir):
    subprocess.run(
        [
            "python3",
            "-m",
            "grpc_tools.protoc",
            f"-I{proto_dir}",
            "--python_out=.",
            "--grpc_python_out=.",
            proto_path,
        ],
        check=True,
    )


def load_modules(base_name):
    if "." not in sys.path:
        sys.path.insert(0, ".")
    pb2 = importlib.import_module(f"{base_name}_pb2")
    pb2_grpc = importlib.import_module(f"{base_name}_pb2_grpc")
    return pb2, pb2_grpc


def main(proto_file, proto_dir, base_name, service_name):
    generate_proto(proto_file, proto_dir)
    pb2, pb2_grpc = load_modules(base_name)

    servicer_class = getattr(pb2_grpc, f"{service_name}Servicer")

    class DynamicServicer(servicer_class):
        def SayHello(self, request, context):
            return pb2.StringValue(value="Hello, " + request.value)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_servicer_func = getattr(pb2_grpc, f"add_{service_name}Servicer_to_server")
    add_servicer_func(DynamicServicer(), server)

    server.add_insecure_port("[::]:50051")
    server.start()
    print("Server started on 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    proto_dir = "proto"
    proto_file = os.path.join(proto_dir, "greeter.proto")
    base_name = "greeter"
    service_name = "Greeter"
    main(proto_file, proto_dir, base_name, service_name)
