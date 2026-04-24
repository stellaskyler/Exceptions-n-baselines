from pathlib import Path

from scripts.validate_changed_records import _iter_yaml_files


def test_iter_yaml_files_supports_yaml_and_yml(tmp_path: Path) -> None:
    records_dir = tmp_path / 'records'
    records_dir.mkdir()
    yaml_file = records_dir / 'record-a.yaml'
    yml_file = records_dir / 'record-b.yml'
    txt_file = records_dir / 'ignore.txt'

    yaml_file.write_text('id: a')
    yml_file.write_text('id: b')
    txt_file.write_text('id: c')

    discovered = sorted(path.name for path in _iter_yaml_files(records_dir))

    assert discovered == ['record-a.yaml', 'record-b.yml']
