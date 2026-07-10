from __future__ import annotations

ERRORS: dict[str, dict[str, int | str]] = {
    "validation_error": {"http": 400, "code": 1001, "key": "errors.codes.1001"},
    "not_found": {"http": 404, "code": 1002, "key": "errors.codes.1002"},
    "not_authenticated": {"http": 401, "code": 2001, "key": "errors.raw.not_authenticated"},
    "invalid_credentials": {"http": 401, "code": 2001, "key": "errors.raw.invalid_credentials"},
    "token_invalid": {"http": 401, "code": 2001, "key": "errors.raw.token_invalid"},
    "user_not_found": {"http": 401, "code": 2001, "key": "errors.raw.user_not_found"},
    "twofa_required": {"http": 401, "code": 2003, "key": "errors.raw.twofa_required"},
    "twofa_invalid": {"http": 401, "code": 2004, "key": "errors.raw.twofa_invalid"},
    "system_not_initialized": {"http": 403, "code": 3001, "key": "errors.codes.3001"},
    "system_already_initialized": {"http": 403, "code": 3003, "key": "errors.codes.3003"},
    "publish_failed": {"http": 500, "code": 4001, "key": "errors.codes.4001"},
    "initialization_failed": {"http": 500, "code": 5000, "key": "errors.codes.5000"},
    "invalid_model_output": {"http": 400, "code": 4101, "key": "errors.labels.invalid_model_output"},
    "qa_circuit_open": {"http": 400, "code": 4102, "key": "errors.labels.qa_circuit_open"},
    "budget_exhausted": {"http": 400, "code": 4103, "key": "errors.labels.budget_exhausted"},
    "task_aborted": {"http": 400, "code": 4104, "key": "errors.labels.task_aborted"},
    "llm_request_failed": {"http": 500, "code": 4201, "key": "errors.labels.llm_request_failed"},
    "llm_timeout": {"http": 504, "code": 4202, "key": "errors.labels.llm_timeout"},
    "embedding_failed": {"http": 500, "code": 4301, "key": "errors.labels.embedding_failed"},
    "container_restart": {"http": 500, "code": 5001, "key": "errors.labels.container_restart"},
}


def key_for_code(code: int) -> str | None:
    for item in ERRORS.values():
        if item["code"] == code:
            return str(item["key"])
    if 1000 <= code < 6000:
        return f"errors.codes.{code}"
    return None


def get_error(error_id: str) -> dict[str, int | str]:
    return ERRORS.get(error_id, ERRORS["validation_error"])
