from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Option:
    name: str
    description: str
    argument: type = str
    default: Any = None
    validator: Callable[[Any], bool] | None = None

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, str):
            return __o == self.name
        return super().__eq__(__o)

    def __post_init__(self) -> None:
        assert not self.name.startswith("__"), "Name cannot start with dunder"


@dataclass
class Data:
    name: str
    required: bool = True
    file: bool = False
    validator: Callable[[Any], bool] | None = None

    def __post_init__(self) -> None:
        assert not self.name.startswith("__"), "Name cannot start with dunder"


class ReturnData:
    def __init__(self) -> None:
        self.__names__: dict[str, type] = {}

    def __repr__(self) -> str:
        copy: dict[str, tuple[str, Any]] = {}
        for name in self.__names__:
            copy[name] = (self.__names__[name].__name__, getattr(self, name))
        return copy.__repr__()

    def __setattr__(self, __name: str, __value: Any) -> None:
        if hasattr(self, "__names__"):
            self.__names__[__name] = type(__value)
        return super(ReturnData, self).__setattr__(__name, __value)


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
                    argument=str,
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
                _usage += f"\n --{option.name}{f'=<{option.argument.__name__}>' if option.argument else ''}\t{option.description}"
        return _usage

    def parse(self) -> ReturnData:
        data = ReturnData()
        for i, arg in enumerate(self.args):
            if arg.startswith("--"):
                arg = arg.replace("--", "")
                value = ""
                if "=" in arg:
                    try:
                        arg, value = arg.split("=")
                    except ValueError:
                        print(self.usage())
                        exit(1)
                if arg == "help" or arg == "h":
                    if value:
                        options = [
                            option
                            for option in self.options
                            if value in option.name or value in option.description
                        ]
                        _usage = "options:"
                        for option in options:
                            _usage += f"\n --{option.name}{f'=<{option.argument}>' if option.argument else ''}\t{option.description}"
                        print(_usage)
                    else:
                        print(self.usage())
                    exit(0)
                if arg not in self.options and arg.replace("no-", "") not in self.options:  # type: ignore
                    print(self.usage())
                    exit(1)
                if arg.startswith("no-"):
                    if value:
                        print(self.usage())
                        exit(1)
                    arg = arg.replace("no-", "")
                    setattr(data, arg, False)
                else:
                    if value:
                        try:
                            opt = [
                                option for option in self.options if option.name == arg
                            ]
                            _type = opt[0].argument
                            setattr(
                                data,
                                arg,
                                _type(value),
                            )
                        except ValueError:
                            print(self.usage())
                            exit(1)
                    else:
                        setattr(data, arg, True)
                if getattr(data, arg) is None:
                    print(self.usage())
                    exit(1)
            else:
                if self.data:
                    _data = " ".join(self.args[i : len(self.args)])
                    if self.data.file:
                        try:
                            setattr(data, arg, open(_data, "rb+"))
                        except FileNotFoundError:
                            print(f"Cannot open file '{_data}': No such file")
                            exit(1)
                    else:
                        setattr(data, arg, _data)
                    break
                else:
                    print(self.usage())
                    exit(1)
        if self.data:
            if not getattr(data, "data") and self.data.required:
                print(self.usage())
                exit(1)
        for option in self.options:
            if option.name not in data.__names__ and option.default:
                setattr(data, option.name, option.default)
        return data
