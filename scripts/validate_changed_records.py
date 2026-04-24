from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import yaml
from jsonschema import validate


SUPPORTED_YAML_EXTENSIONS = ("*.yaml", "*.yml")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _iter_yaml_files(data_dir: Path):
    for pattern in SUPPORTED_YAML_EXTENSIONS:
        yield from data_dir.rglob(pattern)


def main() -> None:
    mappings = [
        (Path('baseline-catalog/baselines'), Path('baseline-catalog/schemas/baseline.schema.json')),
        (Path('baseline-catalog/controls'), Path('baseline-catalog/schemas/control.schema.json')),
        (Path('asset-register/assets/repo'), Path('asset-register/schemas/asset.schema.json')),
        (Path('exception-registry/exceptions'), Path('exception-registry/schemas/exception.schema.json')),
    ]
    for data_dir, schema_path in mappings:
        schema = _load_json(schema_path)
        for file in _iter_yaml_files(data_dir):
            validate(instance=_load_yaml(file), schema=schema)
            print(f'validated {file}')


if __name__ == '__main__':
    main()
