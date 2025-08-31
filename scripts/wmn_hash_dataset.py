"""Hashing utilities for WhatsMyName JSON data files."""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional

from wmn_base import WMNBase
from wmn_constants import (
    DEFAULT_JSON_ENCODING,
    HASH_DISPLAY_LENGTH,
    HASH_FILE_EXTENSION,
)
from wmn_exceptions import WMNError, WMNFileError, WMNHashError


class HashStatus(Enum):
    NEW = auto()
    UPDATED = auto()
    UNCHANGED = auto()


@dataclass(frozen=True)
class HashResult:
    file: Path
    status: HashStatus
    new_hash: str
    previous_hash: Optional[str]


class WMNDataHasher(WMNBase):
    """Generate and update SHA256 hash files for JSON data."""

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def _compute_sha256(data: str) -> str:
        """Compute SHA256 hex digest using default encoding."""
        try:
            return hashlib.sha256(data.encode(DEFAULT_JSON_ENCODING)).hexdigest()
        except (
            UnicodeEncodeError,
            ValueError,
            AttributeError,
            TypeError,
        ) as error:
            raise WMNHashError(f"Failed to compute SHA256 hash: {error}") from error

    @staticmethod
    def _get_hash_file_path(target_file: Path) -> Path:
        """Return associated .sha256 file path for target file."""
        return target_file.with_suffix(target_file.suffix + HASH_FILE_EXTENSION)

    def update_hash_file(self, target_file: Path, data: str) -> HashResult:
        """Compute SHA256, update hash file if needed, and return a structured result. No logging here; callers decide how to report."""
        new_hash = self._compute_sha256(data)
        hash_file = self._get_hash_file_path(target_file)

        try:
            previous_hash = self.read_file_content(hash_file).strip()
        except WMNFileError:
            previous_hash = None

        if previous_hash == new_hash:
            return HashResult(
                file=target_file,
                status=HashStatus.UNCHANGED,
                new_hash=new_hash,
                previous_hash=previous_hash,
            )

        try:
            self.write_file_content(hash_file, new_hash + "\n")
        except WMNFileError as error:
            raise WMNHashError(
                f"Failed to write hash file for {target_file.name}: {error}"
            ) from error

        return HashResult(
            file=target_file,
            status=HashStatus.NEW if previous_hash is None else HashStatus.UPDATED,
            new_hash=new_hash,
            previous_hash=previous_hash,
        )


def main() -> int:
    """Entry point for command-line hashing workflow with top-level logging."""

    hasher = WMNDataHasher()
    logger = hasher.logger

    try:
        results = [
            hasher.update_hash_file(hasher.data_path, hasher.data_raw),
            hasher.update_hash_file(hasher.schema_path, hasher.schema_raw),
        ]
    except WMNError as error:
        logger.error("%s", error)
        return 1
    except Exception:
        logger.exception("Unexpected error during hashing")
        return 1

    hashes_changed = False

    for result in results:
        filename = result.file.name

        if result.status is HashStatus.UNCHANGED:
            logger.info("No hash change for %s", filename)
        elif result.status is HashStatus.NEW:
            hashes_changed = True
            logger.info("Generated new hash for %s", filename)
        elif result.status is HashStatus.UPDATED:
            hashes_changed = True
            old_hash = (result.previous_hash or "")[:HASH_DISPLAY_LENGTH]
            new_hash = result.new_hash[:HASH_DISPLAY_LENGTH]
            logger.info(
                "Hash updated for %s: %s... -> %s...",
                filename,
                old_hash,
                new_hash,
            )
        else:
            logger.error(
                "Unexpected hash status '%s' for %s",
                result.status,
                filename,
            )
            return 1

    logger.info(
        "SHA256 hash files %s",
        "updated successfully" if hashes_changed else "are up to date",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
