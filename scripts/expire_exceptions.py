from __future__ import annotations

from datetime import date
from pathlib import Path
import yaml


def main() -> None:
    today = date.today()
    for file in Path('exception-registry/exceptions').rglob('*.yaml'):
        data = yaml.safe_load(file.read_text())
        if data.get('state') != 'active':
            continue
        if today > date.fromisoformat(str(data['valid_until'])):
            data['state'] = 'expired'
            file.write_text(yaml.safe_dump(data, sort_keys=False))
            print(f'expired {file}')


if __name__ == '__main__':
    main()
