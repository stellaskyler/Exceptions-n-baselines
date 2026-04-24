from importlib.util import module_from_spec, spec_from_file_location

spec = spec_from_file_location('state_mapper', 'integration-servicenow-github/app/state_mapper.py')
state_mapper = module_from_spec(spec)
spec.loader.exec_module(state_mapper)


def test_state_mapping_active() -> None:
    assert state_mapper.to_github_state('implemented_active') == 'active'
