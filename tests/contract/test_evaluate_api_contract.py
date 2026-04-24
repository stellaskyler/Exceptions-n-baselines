import json
from pathlib import Path
from jsonschema import validate


def test_evaluate_examples_conform() -> None:
    req_schema = json.loads(Path('policy-engine/contracts/evaluation-request.schema.json').read_text())
    rsp_schema = json.loads(Path('policy-engine/contracts/evaluation-response.schema.json').read_text())
    req = json.loads(Path('policy-engine/contracts/examples/evaluate.request.json').read_text())
    rsp = json.loads(Path('policy-engine/contracts/examples/evaluate.response.json').read_text())
    validate(instance=req, schema=req_schema)
    validate(instance=rsp, schema=rsp_schema)
