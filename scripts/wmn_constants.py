"""Common constants for WhatsMyName scripts."""

from typing import Final

# File paths and names
DEFAULT_DATA: Final[str] = "wmn-data.json"
DEFAULT_SCHEMA: Final[str] = "wmn-data-schema.json"

# File format and encoding
DEFAULT_JSON_INDENT: Final[int] = 2
DEFAULT_JSON_ENCODING: Final[str] = "utf-8"
DEFAULT_JSON_ENSURE_ASCII: Final[bool] = False
HASH_FILE_EXTENSION: Final[str] = ".sha256"

# JSON schema validation
SITES_KEY: Final[str] = "sites"
NAME_KEY: Final[str] = "name"
AUTHORS_KEY: Final[str] = "authors"
CATEGORIES_KEY: Final[str] = "categories"
HEADERS_KEY: Final[str] = "headers"
PROPERTIES_KEY: Final[str] = "properties"
ITEMS_KEY: Final[str] = "items"

# Hash display length for truncated display
HASH_DISPLAY_LENGTH: Final[int] = 8

# Logging
LOGGER_NAME: Final[str] = "wmn"
