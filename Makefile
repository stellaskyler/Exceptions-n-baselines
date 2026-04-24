.PHONY: validate-schemas test-unit test-contract test-integration test all

validate-schemas:
	python scripts/validate_changed_records.py

test-unit:
	pytest tests/unit -q

test-contract:
	pytest tests/contract -q

test-integration:
	pytest tests/integration -q

test: test-unit test-contract test-integration

all: validate-schemas test
