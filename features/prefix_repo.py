from __future__ import annotations
from typing import Optional
from features.firebase_client import get_ref

class PrefixRepo:
    ROOT = "prefixes"
    DEFAULT = "!"

    def get(self, guild_id: int) -> str:
        data = get_ref(f"{self.ROOT}/{guild_id}").get()
        if not data:
            return self.DEFAULT
        return str(data.get("prefix", self.DEFAULT))

    def set(self, guild_id: int, prefix: str) -> None:
        get_ref(f"{self.ROOT}/{guild_id}").set({"prefix": prefix})

    def clear(self, guild_id: int) -> None:
        get_ref(f"{self.ROOT}/{guild_id}").delete()