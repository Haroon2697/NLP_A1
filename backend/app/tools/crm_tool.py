"""
CRM Tool (Bonus) — Stores, retrieves, and updates user profiles across sessions.
Persists to a local JSON file so the assistant can greet returning users by name.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("fitzone.tools.crm")

# Default persistence path
CRM_STORE_PATH = Path(__file__).resolve().parents[2] / "data" / "crm_store.json"


class CRMTool:
    """
    Stores and retrieves user information (name, preferences, past interactions)
    keyed by session or user ID. Persists to a local JSON file.
    """

    name = "crm_lookup"
    description = (
        "Manages user profiles for FitZone Gym members. Can store, retrieve, or update "
        "user information including name, contact details, preferences, and interaction notes. "
        "Use this to greet returning users by name and recall their past inquiries."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "The CRM action: 'get' (retrieve user), 'set' (create new user), or 'update' (modify existing user).",
                "enum": ["get", "set", "update"],
            },
            "user_id": {
                "type": "string",
                "description": "Unique user or session identifier.",
            },
            "data": {
                "type": "object",
                "description": (
                    "User data to store or update. Can include fields like: "
                    "name, email, phone, preferred_plan, interests, notes, "
                    "fitness_goals, preferred_classes."
                ),
            },
        },
        "required": ["action", "user_id"],
    }

    def __init__(self, store_path: Optional[Path] = None) -> None:
        self.store_path = store_path or CRM_STORE_PATH
        self._lock = threading.Lock()
        self._store: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Loads the CRM store from disk."""
        try:
            if self.store_path.exists():
                with open(self.store_path, "r", encoding="utf-8") as f:
                    self._store = json.load(f)
                logger.info(f"CRM: Loaded {len(self._store)} user profiles from {self.store_path}")
            else:
                self._store = {}
        except Exception as exc:
            logger.error(f"CRM: Failed to load store: {exc}")
            self._store = {}

    def _save(self) -> None:
        """Persists the CRM store to disk."""
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(self._store, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.error(f"CRM: Failed to save store: {exc}")

    async def execute(self, arguments: Dict[str, Any] | None = None, **kwargs) -> Dict[str, Any]:
        """Executes a CRM action (get, set, or update)."""
        args = dict(arguments or {})
        args.update(kwargs)
        action = str(args.get("action", "")).lower().strip()
        user_id = str(args.get("user_id", "")).strip()
        data = args.get("data", {})

        if not user_id:
            return {"success": False, "error": "user_id is required."}

        if action == "get":
            return self._get_user(user_id)
        elif action == "set":
            return self._set_user(user_id, data)
        elif action == "update":
            return self._update_user(user_id, data)
        else:
            return {
                "success": False,
                "error": f"Unknown action '{action}'. Use 'get', 'set', or 'update'.",
            }

    def _get_user(self, user_id: str) -> Dict[str, Any]:
        """Retrieves a user profile."""
        with self._lock:
            profile = self._store.get(user_id)
            if profile:
                return {
                    "success": True,
                    "user_id": user_id,
                    "profile": profile,
                    "is_returning_user": True,
                }
            return {
                "success": True,
                "user_id": user_id,
                "profile": None,
                "is_returning_user": False,
                "message": "No profile found for this user. This is a new visitor.",
            }

    def _set_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new user profile."""
        if not data:
            return {"success": False, "error": "Data payload is required to create a profile."}

        with self._lock:
            import datetime
            profile = {
                **data,
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                "interaction_count": 1,
            }
            self._store[user_id] = profile
            self._save()

        return {
            "success": True,
            "user_id": user_id,
            "action": "created",
            "profile": profile,
        }

    def _update_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing user profile. Merges new data with existing."""
        if not data:
            return {"success": False, "error": "Data payload is required for updates."}

        with self._lock:
            import datetime
            existing = self._store.get(user_id, {})
            existing.update(data)
            existing["updated_at"] = datetime.datetime.now().isoformat()
            existing["interaction_count"] = existing.get("interaction_count", 0) + 1
            self._store[user_id] = existing
            self._save()

        return {
            "success": True,
            "user_id": user_id,
            "action": "updated",
            "profile": existing,
        }
