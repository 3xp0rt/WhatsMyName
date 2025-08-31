"""Shared exception types for WhatsMyName scripts."""


class WMNError(Exception):
    """Base exception for WhatsMyName tools."""

    pass


class WMNFileError(WMNError):
    """File IO error for read/write/permissions."""

    pass


class WMNValidationError(WMNError):
    """Data or schema validation error."""

    pass


class WMNFormatError(WMNError):
    """Formatting error like invalid JSON."""

    pass


class WMNSchemaError(WMNError):
    """Schema structure or parsing error."""

    pass


class WMNHashError(WMNError):
    """Hash computation or file generation error."""

    pass
