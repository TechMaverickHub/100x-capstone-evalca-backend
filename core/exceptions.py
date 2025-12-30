from typing import Dict, List

from fastapi import Request, HTTPException, FastAPI, status
from fastapi.exceptions import RequestValidationError

from core.global_constants import ErrorKeys
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
            schema=errors,
            message="Validation failed.",
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

        return response_schema(
            schema=schema,
            message="Something went wrong. Please try again later.",
            status_code=exc.status_code,
        )
