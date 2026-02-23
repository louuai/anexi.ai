from contextvars import ContextVar


CORRELATION_ID_HEADER = "x-correlation-id"
REQUEST_ID_HEADER = "x-request-id"

_correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    return _correlation_id_var.get()


def set_correlation_id(value: str) -> None:
    _correlation_id_var.set(value or "")

