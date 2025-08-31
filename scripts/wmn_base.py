"""Base utilities shared by WhatsMyName scripts."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from wmn_constants import DEFAULT_DATA, DEFAULT_JSON_ENCODING, DEFAULT_SCHEMA
from wmn_exceptions import WMNFileError, WMNFormatError
from wmn_logging import setup_logging


class WMNBase:
    """Base class providing common paths, logging, and IO operations."""

    def __init__(
        self,
        data_path: str = DEFAULT_DATA,
        schema_path: str = DEFAULT_SCHEMA,
    ) -> None:
        """Initialize base paths and logger."""
        self.data_path = Path(data_path)
        self.schema_path = Path(schema_path)
        self.logger = setup_logging()

        self._data: Optional[Dict[str, Any]] = None
        self._schema: Optional[Dict[str, Any]] = None
        self._data_raw: Optional[str] = None
        self._schema_raw: Optional[str] = None

    def read_file_content(self, file_path: Path) -> str:
        """Read raw content from a file."""
        try:
            return file_path.read_text(encoding=DEFAULT_JSON_ENCODING)
        except FileNotFoundError as error:
            raise WMNFileError(f"File not found: {file_path}") from error
        except IsADirectoryError as error:
            raise WMNFileError(f"Path is not a file: {file_path}") from error
        except PermissionError as error:
            raise WMNFileError(f"Permission denied: {file_path}") from error
        except UnicodeDecodeError as error:
            raise WMNFileError(
                f"Decoding error using {DEFAULT_JSON_ENCODING} "
                f"for {file_path}: {error}"
            ) from error

    def parse_json_data(
        self,
        data: str,
        file_path: Path,
    ) -> Union[Dict[str, Any], List[Any]]:
        """Parse JSON string."""
        try:
            return json.loads(data)
        except json.JSONDecodeError as error:
            raise WMNFormatError(
                f"Invalid JSON in {file_path} at line {error.lineno}, "
                f"column {error.colno}: {error.msg}"
            ) from error
        except TypeError as error:
            raise WMNFormatError(
                f"Invalid input for JSON parsing in {file_path}: {error}"
            ) from error

    def write_file_content(
        self,
        file_path: Path,
        content: str,
        encoding: str = DEFAULT_JSON_ENCODING,
    ) -> None:
        """Write content to a file."""
        try:
            file_path.write_text(content, encoding=encoding)
            if file_path == self.data_path:
                self._data_raw = content
                self._data = None
            elif file_path == self.schema_path:
                self._schema_raw = content
                self._schema = None
        except FileNotFoundError as error:
            raise WMNFileError(f"Directory not found for path: {file_path}") from error
        except IsADirectoryError as error:
            raise WMNFileError(
                f"Path is a directory, not a file: {file_path}"
            ) from error
        except PermissionError as error:
            raise WMNFileError(f"Permission denied: {file_path}") from error
        except UnicodeEncodeError as error:
            raise WMNFileError(
                f"Encoding error using {encoding} for {file_path}: {error}"
            ) from error
        except OSError as error:
            raise WMNFileError(
                f"OS error while writing {file_path}: {error}"
            ) from error

    @property
    def data_raw(self) -> str:
        """Raw JSON string for data file with auto-loading."""
        if self._data_raw is None:
            try:
                self._data_raw = self.read_file_content(self.data_path)
            except WMNFileError as error:
                self.logger.error(
                    "Failed to read data file %s: %s",
                    self.data_path,
                    error,
                )
                raise
        return self._data_raw

    @data_raw.setter
    def data_raw(self, value: Optional[str]) -> None:
        self._data_raw = value
        self._data = None

    @property
    def schema_raw(self) -> str:
        """Raw JSON string for schema file with auto-loading."""
        if self._schema_raw is None:
            try:
                self._schema_raw = self.read_file_content(self.schema_path)
            except WMNFileError as error:
                self.logger.error(
                    "Failed to read schema file %s: %s",
                    self.schema_path,
                    error,
                )
                raise
        return self._schema_raw

    @schema_raw.setter
    def schema_raw(self, value: Optional[str]) -> None:
        self._schema_raw = value
        self._schema = None

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """Parsed JSON object for data file with auto-parsing."""
        if self._data is None:
            raw_json = self.data_raw
            try:
                parsed_json = self.parse_json_data(raw_json, self.data_path)
            except WMNFormatError as error:
                self.logger.error(
                    "Failed to parse data file %s: %s",
                    self.data_path,
                    error,
                )
                raise
            self._data = parsed_json
        return self._data

    @data.setter
    def data(self, value: Optional[Dict[str, Any]]) -> None:
        self._data = value

    @property
    def schema(self) -> Optional[Dict[str, Any]]:
        """Parsed JSON object for schema file with auto-parsing."""
        if self._schema is None:
            raw_json = self.schema_raw
            try:
                parsed_json = self.parse_json_data(raw_json, self.schema_path)
            except WMNFormatError as error:
                self.logger.error(
                    "Failed to parse schema file %s: %s",
                    self.schema_path,
                    error,
                )
                raise
            self._schema = parsed_json
        return self._schema

    @schema.setter
    def schema(self, value: Optional[Dict[str, Any]]) -> None:
        self._schema = value
