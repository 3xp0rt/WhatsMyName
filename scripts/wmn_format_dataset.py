"""Utilities to format WhatsMyName data and schema JSON files."""

import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List

from wmn_base import WMNBase
from wmn_constants import (
    AUTHORS_KEY,
    CATEGORIES_KEY,
    DEFAULT_JSON_ENSURE_ASCII,
    DEFAULT_JSON_INDENT,
    HEADERS_KEY,
    ITEMS_KEY,
    NAME_KEY,
    PROPERTIES_KEY,
    SITES_KEY,
)
from wmn_exceptions import WMNError, WMNFormatError, WMNSchemaError


class WMNDataFormatter(WMNBase):
    """Formatter for WhatsMyName JSON data."""

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def _sort_array_alphabetically(array: List[str]) -> List[str]:
        """Sort strings alphabetically case-insensitively."""
        return sorted(array, key=str.casefold)

    @staticmethod
    def _sort_sites_by_name(sites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort sites by name case-insensitively."""
        return sorted(sites, key=lambda site: str(site.get(NAME_KEY, "")).casefold())

    @staticmethod
    def _sort_site_headers(site_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return site copy with headers sorted by name."""
        result = site_data.copy()

        headers = result.get(HEADERS_KEY)
        if headers and isinstance(headers, dict):
            result[HEADERS_KEY] = dict(
                sorted(
                    headers.items(),
                    key=lambda item: str(item[0]).casefold(),
                )
            )

        return result

    @staticmethod
    def _reorder_site_keys(
        site_data: Dict[str, Any], key_order: List[str]
    ) -> Dict[str, Any]:
        """Return site dict with keys in schema-defined order."""
        result: Dict[str, Any] = {}

        unknown_keys = [key for key in site_data.keys() if key not in key_order]
        if unknown_keys:
            raise WMNFormatError(f"Unknown keys found in site data: {unknown_keys}")

        for key in key_order:
            if key in site_data:
                result[key] = site_data[key]

        return result

    def format_schema(self) -> str:
        """Return formatted schema JSON string."""
        try:
            return json.dumps(
                self.schema,
                indent=DEFAULT_JSON_INDENT,
                ensure_ascii=DEFAULT_JSON_ENSURE_ASCII,
            )
        except (TypeError, ValueError, RecursionError) as error:
            raise WMNFormatError(f"Schema is not JSON-serializable: {error}") from error

    def format_data(self) -> str:
        """Return formatted data JSON string per schema."""
        self._format_string_array(AUTHORS_KEY)
        self._format_string_array(CATEGORIES_KEY)
        self._format_sites()

        try:
            return json.dumps(
                self.data,
                indent=DEFAULT_JSON_INDENT,
                ensure_ascii=DEFAULT_JSON_ENSURE_ASCII,
            )
        except (TypeError, ValueError, RecursionError) as error:
            raise WMNFormatError(f"Data is not JSON-serializable: {error}") from error

    def _get_site_key_order(self) -> List[str]:
        """Extract key order from schema for site objects."""
        site_schema = (
            self.schema.get(PROPERTIES_KEY, {})
            .get(SITES_KEY, {})
            .get(ITEMS_KEY, {})
            .get(PROPERTIES_KEY)
        )

        if site_schema is None:
            raise WMNSchemaError("Site schema properties not found in schema")
        if not isinstance(site_schema, dict):
            raise WMNSchemaError(
                f"Site schema properties must be an object, "
                f"got {type(site_schema).__name__}"
            )

        return list(site_schema.keys())

    def _format_string_array(self, key: str) -> None:
        """Sort string array alphabetically if present."""
        array_data = self.data.get(key)
        if array_data is None:
            raise WMNFormatError(f"'{key}' is required but not found")
        if not isinstance(array_data, list) or not array_data:
            raise WMNFormatError(f"'{key}' must be a non-empty list")
        if not all(isinstance(item, str) and item.strip() for item in array_data):
            raise WMNFormatError(f"'{key}' must contain non-empty strings")
        self.data[key] = self._sort_array_alphabetically(array_data)

    def _format_site(
        self, site_data: Dict[str, Any], key_order: List[str]
    ) -> Dict[str, Any]:
        """Format one site with sorted headers and ordered keys."""
        formatted_site = self._sort_site_headers(site_data)
        formatted_site = self._reorder_site_keys(formatted_site, key_order)
        return formatted_site

    def _format_sites(self) -> None:
        """Sort and format site data per schema."""
        sites = self.data.get(SITES_KEY)
        if not isinstance(sites, list):
            raise WMNFormatError(
                f"'{SITES_KEY}' must be a list, got {type(sites).__name__}"
            )

        sorted_sites = self._sort_sites_by_name(sites)
        key_order = self._get_site_key_order()
        self.data[SITES_KEY] = [
            self._format_site(site_data, key_order) for site_data in sorted_sites
        ]

    def format_file(
        self, formatter: Callable[[], str], raw_data: str, file_path: Path
    ) -> bool:
        """Format content and write if changed, return True if modified."""
        try:
            formatted_data = formatter()

            if raw_data != formatted_data:
                self.write_file_content(file_path, formatted_data)
                return True
            return False

        except WMNError:
            raise
        except Exception as error:
            raise WMNFormatError(
                f"Unexpected error formatting {file_path.name}"
            ) from error


def main() -> int:
    """Run the formatting workflow."""
    formatter = WMNDataFormatter()
    logger = formatter.logger

    try:
        data_changed = formatter.format_file(
            formatter.format_data, formatter.data_raw, formatter.data_path
        )
        logger.info(
            "%s %s",
            formatter.data_path.name,
            "updated and formatted" if data_changed else "already formatted",
        )

        schema_changed = formatter.format_file(
            formatter.format_schema, formatter.schema_raw, formatter.schema_path
        )
        logger.info(
            "%s %s",
            formatter.schema_path.name,
            "updated and formatted" if schema_changed else "already formatted",
        )

        logger.info(
            "JSON files %s",
            (
                "updated and formatted successfully"
                if (data_changed or schema_changed)
                else "are already formatted"
            ),
        )
        return 0

    except WMNError as error:
        logger.error("%s", error)
        return 1
    except Exception as error:
        logger.exception("Unexpected error during formatting: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
