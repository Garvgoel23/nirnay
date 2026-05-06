"""
Local file storage backend.
Abstracts file operations for uploaded documents and exports.
"""
import logging
import os
import shutil
from typing import Optional

logger = logging.getLogger(__name__)


class StorageBackend:
    """Abstract interface for file storage."""

    def save(self, file_bytes: bytes, path: str) -> str:
        raise NotImplementedError

    def read(self, path: str) -> bytes:
        raise NotImplementedError

    def exists(self, path: str) -> bool:
        raise NotImplementedError

    def delete(self, path: str) -> bool:
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    """Stores files on the local filesystem."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or os.getenv("LOCAL_STORAGE_PATH", "./data/uploads")
        os.makedirs(self.base_path, exist_ok=True)

    def save(self, file_bytes: bytes, path: str) -> str:
        """Save file bytes to local filesystem."""
        full_path = os.path.join(self.base_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(file_bytes)

        logger.info(f"Saved file to {full_path} ({len(file_bytes)} bytes)")
        return full_path

    def read(self, path: str) -> bytes:
        """Read file bytes from local filesystem."""
        full_path = os.path.join(self.base_path, path)
        with open(full_path, "rb") as f:
            return f.read()

    def exists(self, path: str) -> bool:
        """Check if file exists."""
        full_path = os.path.join(self.base_path, path)
        return os.path.exists(full_path)

    def delete(self, path: str) -> bool:
        """Delete a file."""
        full_path = os.path.join(self.base_path, path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False


def get_storage_backend() -> StorageBackend:
    """Factory function to get the configured storage backend."""
    backend_type = os.getenv("STORAGE_BACKEND", "local")
    if backend_type == "local":
        return LocalStorageBackend()
    else:
        logger.warning(f"Unknown storage backend '{backend_type}', falling back to local")
        return LocalStorageBackend()
