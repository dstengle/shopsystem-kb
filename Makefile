.PHONY: dev test contract

# One virtualenv per checkout. kb is installed editable here; a client pins a tag.
dev:
	python3 -m venv .venv
	.venv/bin/pip install -e '.[dev]'

test:
	.venv/bin/python -m pytest -q

contract:
	.venv/bin/python -m grpc_tools.protoc -I src --python_out=src --grpc_python_out=src --pyi_out=src src/kb/contract/kb.proto
