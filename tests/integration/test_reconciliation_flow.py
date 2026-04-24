import importlib.util

spec = importlib.util.spec_from_file_location('integration_main', 'integration-servicenow-github/app/main.py')
main_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_mod)


def test_reconciliation_returns_expected_shape() -> None:
    result = main_mod.post_reconcile_run()
    assert set(result.keys()) == {'missing_pr', 'stale_sn_status', 'expired_mismatch', 'field_drift'}
