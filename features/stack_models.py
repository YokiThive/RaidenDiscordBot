from __future__ import annotations
#postpones the evaluation of type annotations
#treating them as strings as the time of function/class
from dataclasses import dataclass, field
#dataclasses make classes that store data easier to write and read
#less prone to bugs
from typing import List, Optional, Dict, Any
import time

@dataclass
class Stack:
    code: str
    size: int
    game: str
    time_text: str
    created_at: int
    channel_id: int = 0 #channel to ping
    reminder: int = 0 #unix time
    reminded: bool = False #prevent duplicates

    #store user info
    """
    Optional[int] is shorthand for int|None,
    it tells that this variable can either hold a specific value or nothing at all
    """
    slots: List[Optional[int]] = field(default_factory=list)
    slot_names: List[Optional[str]] = field(default_factory=list)

    @staticmethod
    def create_stack(code: str, size: int, game: str, time_text: str, id: int, name: str, channel_id: int, reminder: int) -> Stack:
        now = int(time.time())
        slots = [None] * size
        names = [None] * size
        slots[0] = id
        names[0] = name

        return Stack(code=code, size=size, game=game, time_text=time_text, created_at=now, channel_id=channel_id, reminder=reminder, reminded=False, slots=slots, slot_names=names)

    def is_full(self) -> bool:
        return all(uid is not None for uid in self.slots)

    def has_user(self, user_id: int) -> bool:
        return user_id in self.slots

    def empty_index(self) -> Optional[int]:
        # return slow index that is empty
        for i, uid in enumerate(self.slots):
            if uid is None:
                return i
        return None

    def add_user(self, user_id: int, user_name: str) -> bool:
        if self.has_user(user_id):
            return False

        empty_idx = self.empty_index()
        if empty_idx is None:
            return False

        self.slots[empty_idx] = user_id
        self.slot_names[empty_idx] = user_name
        return True

    def slot_label(self, index: int) -> str:
        labels = ["Main/Host", "Duo", "Trio", "Four", "Five"]
        if 0 <= index < len(labels):
            return labels[index]
        return f"Slot {index + 1}"

    def find_user(self, user_id: int) -> Optional[int]:
        for i, uid in enumerate(self.slots):
            if uid == user_id:
                return i
        return None

    def remove_user(self, user_id: int, compact: bool = True) -> bool:
        #compact=True helps with after removal, shifting people left so there are no gaps
        idx = self.find_user(user_id)
        if idx is None:
            return False

        self.slots[idx] = None
        self.slot_names[idx] = None

        if compact:
            self.compact_slots()
        return True

    def compact_slots(self) -> None:
        #move empty users to left size
        pairs = list(zip(self.slots, self.slot_names))
        remained = [(uid, name) for uid, name in pairs if uid is not None]

        #remake lists
        new_slots = [None] * self.size
        new_names = [None] * self.size

        for i, (uid, name) in enumerate(remained):
            new_slots[i] = uid
            new_names[i] = name

        self.slots = new_slots
        self.slot_names = new_names

    def member_ids(self) -> List[int]:
        return [uid for uid in self.slots if uid is not None]

    def is_main(self, user_id: int) -> bool:
        return self.slots and self.slots[0] == user_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "size": self.size,
            "game": self.game,
            "time_text": self.time_text,
            "created_at": self.created_at,
            "channel_id": self.channel_id,
            "reminder": self.reminder,
            "reminded": self.reminded,
            "slots": self.slots,
            "slot_names": self.slot_names,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Stack:
        size = int(data["size"])

        raw_slots = list(data.get("slots", []))
        raw_names = list(data.get("slot_names", []))

        slots = raw_slots + [None] * (size - len(raw_slots))
        slot_names = raw_names + [None] * (size - len(raw_names))

        return Stack(
            code=data.get("code"),
            size=size,
            game=data.get("game", ""),
            time_text=data.get("time_text", ""),
            created_at=int(data.get("created_at", 0)),
            channel_id=int(data.get("channel_id", 0)),
            reminder=int(data.get("reminder", 0)),
            reminded=bool(data.get("reminded", False)),
            slots=slots[:size],
            slot_names=slot_names[:size],
        )