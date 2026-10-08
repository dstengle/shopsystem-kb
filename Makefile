.PHONY: dev test bench contract image image-check

# One virtualenv per checkout. kb is installed editable here; a client pins a tag.
dev:
	python3 -m venv .venv
	.venv/bin/pip install -e '.[dev]'

test:
	.venv/bin/python -m pytest -q -n auto

# The performance bounds at 30,000 artifacts (spec/index.md); not part of test. `bench/bounds.py 3000` for a quick look.
bench:
	.venv/bin/python bench/bounds.py 30000

# kb's image, from this checkout, and the check that it serves a store beside its callers, run against a throwaway
# compose project and its own build of the image; neither is part of test. A release that fails image-check does not ship.
image:
	docker build -t shopsystem-kb:dev .

image-check:
	.venv/bin/python docker/image_check.py

contract:
	.venv/bin/python -m grpc_tools.protoc -I src --python_out=src --grpc_python_out=src --pyi_out=src src/kb/contract/kb.proto
