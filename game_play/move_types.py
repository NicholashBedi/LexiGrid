from enum import Enum, auto
from dataclasses import dataclass

@dataclass
class WordPlay:
    word: str
    row: int
    col: int
    direction: str  # 'H' or 'V'

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