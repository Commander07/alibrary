from __future__ import annotations

import json
import os
import time
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


class __config__:
    def __init__(self) -> None:
        if os.path.exists("alogger.json"):
            pass
        self.filename: str | None = None
        self.format: str = ""
        self.datefmt: str = ""
        self.sep: str = " "

    def __setattr__(self, __name: str, __value: Any) -> None:
        super().__setattr__(__name, __value)
        with open("alogger.json", "w") as f:
            json.dump(self, f)


__config_obj__ = __config__()


def getLogger(name: str | None = None) -> Logger:
    if name:
        return __loggers__.get(name, Logger(name))
    if __main__.__file__ in __loggers__.keys():
        return __loggers__[__main__.__file__]
    logger = Logger(__main__.__file__)
    __loggers__[__main__.__file__] = logger
    return logger


def basicConfig(
    filename: str | None = None,
    format: str = "[{time}] [{name}] [{levelname}] {message}",
    datefmt: str = "%H:%M:%S",
    sep: str = " ",
) -> None:
    config(filename=filename, format=format, datefmt=datefmt, sep=sep)


def config(
    filename: str | None = None,
    format: str | None = None,
    datefmt: str | None = None,
    sep: str | None = None,
) -> None:
    if filename:
        __config_obj__.filename = filename
    if format:
        __config_obj__.format = format
    if datefmt:
        __config_obj__.datefmt = datefmt
    if sep:
        __config_obj__.sep = sep


class Logger:
    def __init__(
        self,
        name: str,
        level: Level = Level.INFO,
        filename: str | None = None,
        format: str = "[{time}] [{name}] [{levelname}] {message}",
        datefmt: str = "%H:%M:%S",
        sep: str = " ",
    ) -> None:
        self.name = name
        self.level = level
        self.filename = filename
        self.format = format
        self.datefmt = datefmt
        self.sep = sep

    def _log(self, level: Level, *msg: str) -> None:
        message = self.format.format(
            time=time.strftime(self.datefmt),
            name=self.name,
            levelname=level.name,
            message=self.sep.join(msg),
        )
        if self.filename:
            with open(self.filename, "a") as f:
                f.write(message)
        print(message)

    def trace(self, *msg: str) -> None:
        self._log(Level.TRACE, *msg)

    def debug(self, *msg: str) -> None:
        self._log(Level.DEBUG, *msg)

    def info(self, *msg: str) -> None:
        self._log(Level.INFO, *msg)

    def warning(self, *msg: str) -> None:
        self._log(Level.WARNING, *msg)

    def error(self, *msg: str) -> None:
        self._log(Level.ERROR, *msg)

    def fatal(self, *msg: str) -> None:
        self._log(Level.FATAL, *msg)
