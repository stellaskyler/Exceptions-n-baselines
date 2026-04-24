class MockServiceNowClient:
    def update_request(self, exception_request_id: str, payload: dict) -> dict:
        return {"exception_request_id": exception_request_id, "updated": True, "payload": payload}
