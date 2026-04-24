import importlib.util

spec = importlib.util.spec_from_file_location('integration_main', 'integration-servicenow-github/app/main.py')
main_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_mod)


def test_sync_creates_and_then_deduplicates() -> None:
    payload = {
        'exception_request_id': 'SN-EXC-001',
        'request_state': 'approved_pending_github',
        'idempotency_key': 'SN-EXC-001:v1',
        'version': 1,
    }
    first = main_mod.post_exceptions_sync(payload)
    second = main_mod.post_exceptions_sync(payload)
    assert first['status'] == 'created'
    assert second['status'] == 'deduplicated'
