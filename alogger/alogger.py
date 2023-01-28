from __future__ import annotations

from enum import Enum, auto
from typing import Any

import __main__


__loggers__: dict[str, Logger] = {}


class Level(Enum):
    NOTSET = auto()
    TRACE = auto()
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    FATAL = auto()


def getLogger(name: str | None = None) -> Logger:
    if name:
        return __loggers__.get(name, Logger(name))
    return __loggers__.get(__main__.__file__, Logger(__main__.__file__))


class Logger:
    def __init__(
        self,
        name: str,
        level: Level = Level.INFO,
        filename: str | None = None,
        format: str = "[{time}] [{name}] [{levelname}] {message}",
        datefmt: str = "%H:%M:%S",
    ) -> None:
        self.name = name
        self.level = level
        self.filename = filename
        self.format = format
        self.datefmt = datefmt

    def _log(self, level: Level, msg: str, *obj: Any) -> None:
        pass
