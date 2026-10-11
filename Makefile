.PHONY: dev test coverage-map coverage-ask bench contract image image-check

# One virtualenv per checkout. kb is installed editable here; a client pins a tag.
dev:
	python3 -m venv .venv
	.venv/bin/pip install -e '.[dev]'

test:
	.venv/bin/python -m pytest -q -n auto

# The map of which test executes which line of src/kb (a per-test context in .coverage-map, git-ignored), made by a
# run of the whole suite under coverage; not part of test. Ask it with `make coverage-ask ARGS="tests-for src/kb/examining.py"`
# or `ARGS="unexecuted"` (tools/coverage_map.py).
coverage-map:
	rm -f .coverage-map*
	PYTHONPATH=tools .venv/bin/python -m pytest -q -n auto -p passed_record --cov --cov-context=test --cov-report=

coverage-ask:
	.venv/bin/python tools/coverage_map.py $(ARGS)

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
