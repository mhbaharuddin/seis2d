from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any
import json
import os

@dataclass
class Project:
    name: str = "Untitled"
    version: str = "0.0.1"
    lines: Dict[str, Any] = field(default_factory=dict)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2)

    @staticmethod
    def load(path: str) -> "Project":
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        p = Project()
        p.name = data.get('name', p.name)
        p.version = data.get('version', p.version)
        p.lines = data.get('lines', {})
        return p
