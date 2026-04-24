import json
from pathlib import Path
from jsonschema import validate


def test_sync_response_schema() -> None:
    schema = json.loads(Path('integration-servicenow-github/contracts/sync-response.schema.json').read_text())
    payload = {
        'status': 'created',
        'correlation': {
            'exception_request_id': 'SN-EXC-0001',
            'version': 1,
            'pull_request_url': 'https://github.com/org/repo/pull/1',
            'exception_record_id': 'EXR-2026-000001',
        },
    }
    validate(instance=payload, schema=schema)
