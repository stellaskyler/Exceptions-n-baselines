from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import hashlib


def main() -> None:
    outdir = Path('artifacts/decision/ASSET-REPO-org-cloud-networking-iac')
    outdir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    payload = {
        'asset_id': 'ASSET-REPO-org-cloud-networking-iac',
        'timestamp': ts,
        'signer': 'placeholder-oidc-principal',
    }
    payload_path = outdir / f'{ts}.json'
    payload_path.write_text(json.dumps(payload, indent=2))
    digest = hashlib.sha256(payload_path.read_bytes()).hexdigest()
    (outdir / f'{ts}.sha256').write_text(digest)
    print(f'published evidence manifest {payload_path}')


if __name__ == '__main__':
    main()
