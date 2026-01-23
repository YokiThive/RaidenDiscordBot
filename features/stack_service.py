from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from features.stack_repo import StackRepository
from features.stack_models import Stack
import random
import string

@dataclass
class Leave:
    ok: bool
    message:str
    action: str
    stack: Optional[Stack] = None
    ping_ids: Optional[List[int]] = None

class StackService:
    def __init__(self, repo: StackRepository):
        self.repo = repo

    def create_code(self, length: int = 4) -> str:
        alphabet = string.ascii_letters + string.digits
        for _ in range(50):
            code = ''.join(random.choices(alphabet, k=length))
            if self.repo.get(code) is None:
                return code
        raise RuntimeError("Could not generate code")

    def leave_stack(self, code: str, user_id: int) -> Leave:
        code = code.strip()
        stk = self.repo.get(code)

        if not stk:
            return Leave(False, "Invalid stack code", "none")

        if not stk.has_user(user_id):
            return Leave(False, "You are not in this stack", "none", stack=stk)

        if stk.is_main(user_id):
            ids = stk.member_ids()
            self.repo.delete(code)
            return Leave(ok=True, message=f"Main host left - stack `{code}` deleted", action="deleted", stack=stk, ping_ids=ids)

        removed = stk.remove_user(user_id, compact=True)
        if not removed:
            return Leave(False, "Failed to leave", "none", stack=stk)

        self.repo.set(stk)
        return Leave(True, f"You left stack `{code}`", "left", stack=stk)