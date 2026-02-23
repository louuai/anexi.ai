import uuid

from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.context import (
    CORRELATION_ID_HEADER,
    REQUEST_ID_HEADER,
    set_correlation_id,
)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        incoming_correlation_id = (
            request.headers.get(CORRELATION_ID_HEADER)
            or request.headers.get(REQUEST_ID_HEADER)
            or str(uuid.uuid4())
        )
        set_correlation_id(incoming_correlation_id)

        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = incoming_correlation_id
        # Keep backward compatibility for existing request-id consumers.
        response.headers[REQUEST_ID_HEADER] = incoming_correlation_id
        return response

