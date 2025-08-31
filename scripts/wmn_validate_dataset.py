"""Validation utilities for WhatsMyName JSON data files."""

import json
import sys
from collections import Counter
from dataclasses import dataclass
from typing import List, Optional

from jsonschema import Draft7Validator, ValidationError
from jsonschema.exceptions import SchemaError
from wmn_base import WMNBase
from wmn_constants import (
    DEFAULT_JSON_ENSURE_ASCII,
    DEFAULT_JSON_INDENT,
    NAME_KEY,
    SITES_KEY,
)
from wmn_exceptions import WMNError, WMNSchemaError


@dataclass(frozen=True)
class WMNValidationModel:
    """Structured representation of a validation error."""

    path: str
    data: Optional[str]
    message: str


class WMNDataValidator(WMNBase):
    """Validator for WhatsMyName JSON data."""

    def __init__(self) -> None:
        super().__init__()

    def _format_validation_error(
        self,
        error: ValidationError,
    ) -> WMNValidationModel:
        """Format ValidationError into structured error detail."""
        message_text = error.message
        path_string = error.json_path
        data_preview: Optional[str] = None

        try:
            if error.absolute_path:
                current_data = self.data
                for segment in error.absolute_path:
                    current_data = current_data[segment]
                if current_data is not None:
                    data_preview = json.dumps(
                        current_data,
                        ensure_ascii=DEFAULT_JSON_ENSURE_ASCII,
                        indent=DEFAULT_JSON_INDENT,
                    )
        except Exception:
            data_preview = None

        return WMNValidationModel(
            path=path_string,
            data=data_preview,
            message=message_text,
        )

    def validate_schema(self) -> List[WMNValidationModel]:
        """Validate data against schema and return list of error details."""
        try:
            validator = Draft7Validator(self.schema)
        except SchemaError as error:
            raise WMNSchemaError(f"Invalid JSON schema: {error}") from error

        return [
            self._format_validation_error(error)
            for error in validator.iter_errors(self.data)
        ]

    def validate_duplicates(self) -> List[str]:
        """Return list of duplicate site names found in data."""
        sites_data = self.data.get(SITES_KEY, [])
        site_names = [site.get(NAME_KEY) for site in sites_data if site.get(NAME_KEY)]
        return [name for name, count in Counter(site_names).items() if count > 1]


def main() -> int:
    """Run validation process and return error code on failure."""
    validator = WMNDataValidator()
    logger = validator.logger

    try:
        schema_errors = validator.validate_schema()
        if schema_errors:
            for error in schema_errors:
                if error.data is not None:
                    logger.error(
                        "Schema violation at %s: %s\nOffending value: %s",
                        error.path,
                        error.message,
                        error.data,
                    )
                else:
                    logger.error(
                        "Schema violation at %s: %s",
                        error.path,
                        error.message,
                    )
            logger.error(
                "JSON schema validation failed with %d error(s)",
                len(schema_errors),
            )
            return 1
        logger.info("JSON schema validation successful")

        duplicate_names = validator.validate_duplicates()
        if duplicate_names:
            logger.error(
                "Duplicate site 'name' values found: %s",
                duplicate_names,
            )
            return 1
        logger.info("No duplicate site names found")

        logger.info("All validations passed successfully")
        return 0

    except WMNError as error:
        logger.error("%s", error)
        return 1
    except Exception as error:
        logger.exception("Unexpected error during validation: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
