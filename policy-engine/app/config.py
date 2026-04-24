from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
BASELINE_DIR = BASE_DIR / "baseline-catalog" / "baselines"
EXCEPTION_DIR = BASE_DIR / "exception-registry" / "exceptions"
ASSET_DIR = BASE_DIR / "asset-register" / "assets" / "repo"
