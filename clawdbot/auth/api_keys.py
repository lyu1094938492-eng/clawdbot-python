"""
API key management and validation
"""

import hashlib
import json
import logging
import os
import secrets
from pathlib import Path
from datetime import UTC, datetime, timedelta

from fastapi import Header, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class APIKey(BaseModel):
    """API key model"""

    key_id: str
    key_hash: str
    raw_key: str | None = None  # Added for plain text storage as requested
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    last_used: datetime | None = None
    permissions: set[str] = Field(default_factory=lambda: {"read", "write"})
    rate_limit: int | None = None  # requests per minute
    enabled: bool = True

    def is_valid(self) -> bool:
        """Check if key is valid"""
        if not self.enabled:
            return False

        if self.expires_at and datetime.now(UTC) > self.expires_at:
            return False

        return True

    def has_permission(self, permission: str) -> bool:
        """Check if key has permission"""
        return permission in self.permissions

    def update_last_used(self) -> None:
        """Update last used timestamp"""
        self.last_used = datetime.now(UTC)


class APIKeyManager:
    """
    Manages API keys with validation and rotation

    Example:
        manager = APIKeyManager()
        key = manager.create_key("my-app", permissions={"read", "write"})
        print(f"API Key: {key}")

        # Later, validate
        if manager.validate_key(provided_key):
            print("Valid key!")
    """

    def __init__(self, storage_path: str = "data/api_keys.json"):
        self._keys: dict[str, APIKey] = {}
        self._hash_to_key: dict[str, str] = {}  # hash -> key_id mapping
        self.storage_path = Path(storage_path)
        self.load_keys()

    def create_key(
        self,
        name: str,
        permissions: set[str] | None = None,
        expires_days: int | None = None,
        rate_limit: int | None = None,
    ) -> str:
        """
        Create a new API key

        Args:
            name: Key name/description
            permissions: Set of permissions
            expires_days: Days until expiration
            rate_limit: Requests per minute limit

        Returns:
            The API key string (format: clb_xxx)
        """
        # Generate secure random key
        key_id = secrets.token_urlsafe(16)
        raw_key = f"clb_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(raw_key)

        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_days)

        # Create APIKey object
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            raw_key=raw_key,  # Store the raw key
            name=name,
            expires_at=expires_at,
            permissions=permissions or {"read", "write"},
            rate_limit=rate_limit,
        )

        # Store
        self._keys[key_id] = api_key
        self._hash_to_key[key_hash] = key_id

        # Persist
        self.save_keys()

        logger.info(f"Created API key: {key_id} for {name}")

        return raw_key

    def validate_key(self, raw_key: str) -> APIKey | None:
        """
        Validate an API key

        Args:
            raw_key: The raw API key string

        Returns:
            APIKey object if valid, None otherwise
        """
        if not raw_key or not raw_key.startswith("clb_"):
            return None

        key_hash = self._hash_key(raw_key)
        key_id = self._hash_to_key.get(key_hash)

        if not key_id:
            return None

        api_key = self._keys.get(key_id)
        if not api_key or not api_key.is_valid():
            return None

        # Update last used
        api_key.update_last_used()

        return api_key

    def revoke_key(self, key_id: str) -> bool:
        """
        Revoke an API key

        Args:
            key_id: Key ID to revoke

        Returns:
            True if revoked, False if not found
        """
        if key_id in self._keys:
            self._keys[key_id].enabled = False
            self.save_keys()
            logger.info(f"Revoked API key: {key_id}")
            return True
        return False

    def delete_key(self, key_id: str) -> bool:
        """
        Permanently delete an API key

        Args:
            key_id: Key ID to delete

        Returns:
            True if deleted, False if not found
        """
        if key_id in self._keys:
            api_key = self._keys[key_id]
            del self._hash_to_key[api_key.key_hash]
            del self._keys[key_id]
            self.save_keys()
            logger.info(f"Deleted API key: {key_id}")
            return True
        return False

    def list_keys(self) -> list[APIKey]:
        """List all API keys"""
        return list(self._keys.values())

    def get_key(self, key_id: str) -> APIKey | None:
        """Get API key by ID"""
        return self._keys.get(key_id)

    def _hash_key(self, raw_key: str) -> str:
        """Hash an API key"""
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def cleanup_expired(self) -> int:
        """
        Remove expired keys

        Returns:
            Number of keys removed
        """
        expired = []
        for key_id, api_key in self._keys.items():
            if api_key.expires_at and datetime.now(UTC) > api_key.expires_at:
                expired.append(key_id)

        for key_id in expired:
            self.delete_key(key_id)

        if expired:
            self.save_keys()

        return len(expired)

    def save_keys(self) -> None:
        """Save keys to storage"""
        try:
            # Create directory if it doesn't exist
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare data
            data = [key.model_dump(mode="json") for key in self._keys.values()]

            # Write to file
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(data)} API keys to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save API keys: {e}")

    def load_keys(self) -> None:
        """Load keys from storage"""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for key_data in data:
                try:
                    # Convert strings to datetime if needed (Pydantic handles ISO strings)
                    api_key = APIKey(**key_data)
                    self._keys[api_key.key_id] = api_key
                    self._hash_to_key[api_key.key_hash] = api_key.key_id
                except Exception as e:
                    logger.error(f"Failed to parse API key data: {e}")

            logger.info(f"Loaded {len(self._keys)} API keys from {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to load API keys: {e}")



# Global API key manager
_api_key_manager: APIKeyManager | None = None


def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()

        # Create default API key if none exist
        if len(_api_key_manager.list_keys()) == 0:
            default_key = _api_key_manager.create_key(
                name="default", permissions={"read", "write", "admin"}
            )
            logger.info(f"Created default API key: {default_key}")
            logger.warning(
                "⚠️  Default API key created. "
                "In production, create proper keys and delete this one."
            )

    return _api_key_manager


# FastAPI dependency
async def verify_api_key(x_api_key: str | None = Header(None)) -> APIKey:
    """
    Verify API key from header

    Use as FastAPI dependency:
        @app.get("/protected")
        async def endpoint(api_key: APIKey = Depends(verify_api_key)):
            ...
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    manager = get_api_key_manager()
    api_key = manager.validate_key(x_api_key)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key
