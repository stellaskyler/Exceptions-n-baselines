from .routes import sync_exception
from .reconciler import run_reconciliation


def post_exceptions_sync(payload: dict) -> dict:
    return sync_exception(payload)


def post_reconcile_run() -> dict:
    result = run_reconciliation()
    return result.__dict__
