import json
from pathlib import Path
import yaml
from jsonschema import validate


def test_exception_sample_matches_schema() -> None:
    schema = json.loads(Path('exception-registry/schemas/exception.schema.json').read_text())
    sample = yaml.safe_load(Path('exception-registry/exceptions/2026/EXR-2026-000184.yaml').read_text())
    validate(instance=sample, schema=schema)
