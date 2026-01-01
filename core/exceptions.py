from typing import Dict, List

from fastapi import Request, HTTPException, FastAPI, status
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from core.global_constants import ErrorKeys, ErrorMessage
from core.utils import response_schema


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Handles Pydantic validation errors (field-level).
        Transforms them into { field_name: [errors...] }.
        """
        errors: Dict[str, List[str]] = {}
        for e in exc.errors():
            field = e["loc"][-1]  # last element is the field name
            msg = e["msg"]
            errors.setdefault(field, []).append(msg)

        return response_schema(
            data=errors,
            message=ErrorMessage.VALIDATION_FAILED.value,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Handles business / non-field errors.
        Expects you to raise with detail={"detail": ["..."]}.
        """

        if isinstance(exc.detail, dict):
            # Already a dict → use as-is
            schema = exc.detail
        else:
            # If a string, wrap into non-field error
            schema = {ErrorKeys.NON_FIELD_ERROR.value: [exc.detail]}

        payload = response_schema(
            message=ErrorMessage.BAD_REQUEST.value,
            data=schema,
            status_code=exc.status_code
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=payload
        )
