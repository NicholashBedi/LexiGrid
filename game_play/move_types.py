from enum import Enum, auto
from dataclasses import dataclass

@dataclass
class WordPlay:
    word: str
    row: int
    col: int
    direction: str  # 'H' or 'V'

    def to_dict(self):
        return {
            "word": self.word,
            "row": self.row,
            "col": self.col,
            "direction": self.direction
        }

    @classmethod
    def from_dict(self, d: dict):
        return WordPlay(
            word=d.get("word", ""),
            row=d.get("row", 0),
            col=d.get("col", 0),
            direction=d.get("direction", "H")
        )

class MoveResult(Enum):
    NEXT = "next"
    END = "end"
    RETRY = "retry"


class MoveOptions(Enum):
    CHALLENGE = "challenge"
    PASS = "pass"
    PLAY = "play"
    SKIP = "skip"
    EXCHANGE = "exchange"
    END = "end"
    SAVE = "save"
