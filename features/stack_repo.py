from __future__ import annotations
from typing import Optional, Dict
from features.firebase_client import get_ref
from features.stack_models import Stack

class StackRepository:
    ROOT = "stacks"

    def get(self, code: str) -> Optional[Stack]:
        data = get_ref(f"{self.ROOT}/{code}").get()
        if not data:
            return None
        return Stack.from_dict(data)

    def set(self, stack: Stack) -> None:
        get_ref(f"{self.ROOT}/{stack.code}").set(stack.to_dict())

    def delete(self, code: str) -> None:
        get_ref(f"{self.ROOT}/{code}").delete()

    def list(self) -> Dict[str, Stack]:
        data = get_ref(self.ROOT).get() or {}
        stacks: Dict[str, Stack] = {}

        for code, raw in data.items():
            try:
                stacks[code] = Stack.from_dict(raw)
            except Exception as e:
                print(f"Failed to load stack '{code}': {e}")
                continue

        return stacks