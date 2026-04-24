from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml


def expire_exceptions(exceptions_dir: Path, today: date) -> tuple[list[Path], list[str]]:
    expired: list[Path] = []
    skipped: list[str] = []
    for file in exceptions_dir.rglob('*.yaml'):
        data = yaml.safe_load(file.read_text())
        if data.get('state') != 'active':
            continue
        valid_until = data.get('valid_until')
        if not valid_until:
            skipped.append(f'skipped {file}: missing valid_until')
            continue
        try:
            expiry_date = date.fromisoformat(str(valid_until))
        except ValueError:
            skipped.append(f'skipped {file}: invalid valid_until={valid_until}')
            continue

        if today > expiry_date:
            data['state'] = 'expired'
            file.write_text(yaml.safe_dump(data, sort_keys=False))
            expired.append(file)
    return expired, skipped


def main() -> None:
    expired, skipped = expire_exceptions(Path('exception-registry/exceptions'), date.today())
    for file in expired:
        print(f'expired {file}')
    for message in skipped:
        print(message, file=sys.stderr)


if __name__ == '__main__':
    main()
