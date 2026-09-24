.PHONY: dev contract

dev:
	pip install -e '.[dev]'

contract:
	python -m grpc_tools.protoc -I src --python_out=src --grpc_python_out=src --pyi_out=src src/kb/contract/kb.proto
