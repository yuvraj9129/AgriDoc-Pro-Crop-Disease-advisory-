from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


class AdvisoryService:
    def __init__(self, data_path: Optional[str] = None) -> None:
        if data_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(os.path.dirname(base_dir), "data", "diseases.json")
        self._data_path = data_path
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self._data_path):
            return {}
        with open(self._data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_advice(self, label: str, crop: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not label:
            return None
        by_label = self._data.get(label)
        if by_label is None:
            return None
        if crop and isinstance(by_label, dict) and "per_crop" in by_label:
            per_crop = by_label.get("per_crop", {})
            specific = per_crop.get(crop)
            if isinstance(specific, dict):
                # Merge crop-specific over base
                base = {k: v for k, v in by_label.items() if k != "per_crop"}
                base.update(specific)
                return base
        # Return base
        if isinstance(by_label, dict):
            return {k: v for k, v in by_label.items() if k != "per_crop"}
        return None


