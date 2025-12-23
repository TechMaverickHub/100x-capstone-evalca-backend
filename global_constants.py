from enum import Enum


class SuccessMessage(str, Enum):
    """Success messages used across the application."""

    RECORD_CREATED = "Record created successfully."
    RECORD_UPDATED = "Record updated successfully."
    RECORD_DELETED = "Record deleted successfully."
    RECORD_RETRIEVED = "Record retrieved successfully."

    LOGIN_SUCCESS = "Login successful."
    LOGOUT_SUCCESS = "Logout successful."


class ErrorMessage(str, Enum):
    """Error messages used across the application."""

    BAD_REQUEST = "Bad request."
    NOT_FOUND = "Record not found."
    SOMETHING_WENT_WRONG = "Something went wrong. Please try again later."

    SERVER_MISCONFIGURED = "Server configuration error: missing GROQ_API_KEY."
    ANSWER_GENERATION_FAILED = "We’re having trouble generating an answer. Please try again."

    EMAIL_ALREADY_EXISTS = "Email already exists."
    INVALID_CREDENTIALS = "Invalid credentials."
    AUTHORIZATION_HEADER_MISSING_OR_INVALID = "Authorization header missing or invalid"
    INVALID_TOKEN = "Invalid or expired token"

    LOGOUT_FAILED = "Logout failed."


class ErrorKeys(str, Enum):
    NON_FIELD_ERROR = "detail"
