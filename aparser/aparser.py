from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import BinaryIO


@dataclass
class Option:
    name: str
    description: str
    argument: str | None = None

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, str):
            return __o == self.name
        return super().__eq__(__o)


@dataclass
class Data:
    name: str
    required: bool = True
    file: bool = False


class Parser:
    def __init__(
        self,
        options: list[Option] | None = None,
        data: Data | None = None,
        args: list[str] = sys.argv,
    ) -> None:
        self.path = args.pop(0)
        self.args = args
        self.data: Data | None = data
        self.options = (
            [
                Option(
                    "help",
                    "print options which contain the given string in their name",
                    argument="string",
                )
            ]
            + options
            if options
            else []
        )

    def usage(self) -> str:
        data = ""
        if self.data:
            if self.data.required:
                data += "<"
            else:
                data += "["
            data += self.data.name
            if self.data.required:
                data += ">"
            else:
                data += "]"
        _usage = ""
        _usage += f"Usage:\t{self.path}{' [options]' if self.options else ''}{f' {data}' if self.data else ''}"
        if self.options:
            _usage += "\noptions:"
            for option in self.options:
                _usage += f"\n --{option.name}{f'=<{option.argument}>' if option.argument else ''}\t{option.description}"
        return _usage

    def parse(self) -> dict[str, str | bool | BinaryIO]:
        data: dict[str, str | bool | BinaryIO] = {}
        for i, arg in enumerate(self.args):
            if arg.startswith("--"):
                arg = arg.replace("--", "")
                value = ""
                if arg == "help" or arg == "h":
                    print(self.usage())
                    exit(0)
                if "=" in arg:
                    try:
                        arg, value = arg.split("=")
                    except ValueError:
                        print(self.usage())
                        exit(1)
                if arg not in self.options and arg.replace("no-", "") not in self.options:  # type: ignore
                    print(self.usage())
                    exit(1)
                if arg.startswith("no-"):
                    if value:
                        print(self.usage())
                        exit(1)
                    arg = arg.replace("no-", "")
                    data[arg] = False
                else:
                    if value:
                        data[arg] = value
                    else:
                        data[arg] = True
                if not data.get(arg):
                    print(self.usage())
                    exit(1)
            else:
                if self.data:
                    _data = " ".join(self.args[i : len(self.args)])
                    if self.data.file:
                        try:
                            data["data"] = open(_data, "rb+")
                        except FileNotFoundError:
                            print(f"Cannot open file '{_data}': No such file")
                            exit(1)
                    else:
                        data["data"] = _data
                    break
                else:
                    print(self.usage())
                    exit(1)
        if self.data:
            if not data.get("data") and self.data.required:
                print(self.usage())
                exit(1)
        return data
