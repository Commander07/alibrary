from __future__ import annotations


import urllib.request as request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from inspect import getframeinfo, stack
from typing import Any, MutableMapping, cast
from urllib.error import HTTPError


@dataclass
class Element:
    tag: str
    attrs: dict[str, str | bool]
    data: str = ""
    inner_html: list[Element] = field(default_factory=list)
    parent: Element | None = None

    def __eq__(self, __o: object) -> bool:
        """
        TODO: remove completely
        def handle_endtag(self, tag: str) -> None:
            ...
                self.index = self.currrent_tags.index(tag)  # type: ignore
            ...
        """
        if isinstance(__o, str):
            return __o == self.tag
        return super().__eq__(__o)


class SelectorSyntaxError(SyntaxError):
    def __init__(self, info: str, query: str, cmd: str) -> None:
        caller = getframeinfo(stack()[3][0])
        code = cast(list[str], caller.code_context)[0]
        query_start = code.find(query) + 1
        query_end = query_start + len(query)
        cmd_start = query.find(cmd)
        cmd_end = cmd_start + len(cmd)
        super().__init__(
            info,
            (
                caller.filename,
                caller.lineno,
                query_start + cmd_start,
                code,
                caller.positions.end_lineno,  # type: ignore
                query_end + cmd_end,
            ),
        )


class Scraper(HTMLParser):
    def __init__(self, *, convert_charrefs: bool = True) -> None:
        self.index = -1
        self.currrent_tags: list[Element] = []
        self.elements: list[Element] = []
        self.classes: dict[str, list[int]] = {}
        self.ids: dict[str, int] = {}
        self.tags: dict[str, list[int]] = {}
        self.attributes: dict[str, list[int]] = {}
        self.data: dict[str, list[int]] = {}
        self.content = ""
        super().__init__(convert_charrefs=convert_charrefs)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.index += 1
        self.currrent_tags.append(
            Element(
                tag,
                dict(
                    cast(
                        list[tuple[str, str | bool]],
                        [(a[0], a[1]) if a[1] else (a[0], True) for a in attrs],
                    )
                ),
            )
        )

        if tag in [
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "source",
            "track",
            "wbr",
        ]:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        index_jmp = self.index - 1
        if tag != self.currrent_tags[self.index].tag:
            self.index = self.currrent_tags.index(tag)  # type: ignore
        self.elements.append(self.currrent_tags[self.index])
        index = len(self.elements) - 1
        tag = self.currrent_tags[self.index].tag
        self.tags.update({tag: self.tags.get(tag, []) + [index]})
        class_atr = self.currrent_tags[self.index].attrs.get("class", False)
        if isinstance(class_atr, str):
            classes = class_atr.split(" ")
            for cls in classes:
                self.classes.update({cls: self.classes.get(cls, []) + [index]})
        id_atr = self.currrent_tags[self.index].attrs.get("id", "")
        if isinstance(id_atr, str) and id_atr:
            self.ids[id_atr] = index
        attrs = list(self.currrent_tags[self.index].attrs.keys())
        for attr in attrs:
            self.attributes.update({attr: self.attributes.get(attr, []) + [index]})
        self.currrent_tags.pop(self.index)
        self.index = index_jmp

    def handle_data(self, data: str) -> None:
        if len(self.currrent_tags) == 0:
            return
        self.currrent_tags[self.index].data = data

    def parse_query(
        self, query: str
    ) -> tuple[list[str], list[str], list[str], list[str], list[str], tuple[Any, ...]]:
        cmds = query.split(" ")
        classes: list[str] = []
        tags: list[str] = []
        attrs: list[str] = []
        id: list[str] = []
        data: list[str] = []
        parent: tuple[Any, ...] = cast(tuple[Any, ...], ())  # return value of self
        for i, cmd in enumerate(cmds):
            if cmd[0] == "(":
                open = True
                end = 0
                inners = 0
                j = i
                while j < len(cmds):
                    if cmds[j][-1] == ")":
                        if inners:
                            inners -= 1
                        else:
                            open = False
                            end = j
                    elif cmds[j][0] == "(":
                        inners += 1
                    j += 1
                if open:
                    raise SyntaxError("'(' was never closed")
                elif parent:
                    raise SyntaxError("Cannot have multiple parents")
                cmds[i] = cmds[i][1:]
                cmds[end] = cmds[end][0:-1]
                parent = self.parse_query(" ".join(cmds[i : end + 1]))
            elif cmd[0] == ".":
                if not cmd[1:]:
                    raise SyntaxError("Missing class name")
                classes.append(cmd[1:])
            elif cmd[0] == "[":
                if cmd[-1] != "]":
                    raise SyntaxError("'[' was never closed")
                if not cmd[1:-1]:
                    raise SyntaxError("Missing attribute name")
                attrs.append(cmd[1:-1])
            elif cmd[0] == "{":
                if cmd[-1] != "}":
                    raise SyntaxError("'{' was never closed")
                if not cmd[1:-1]:
                    raise SyntaxError("Missing data")
                data.append(cmd[1:-1])
            elif cmd[0] == "#":
                if not cmd[1:]:
                    raise SyntaxError("Missing id name")
                if id:
                    raise SyntaxError("Element cannot have multiple ids")
                id = [cmd[1:]]
            else:
                tags.append(cmd)
        return classes, tags, attrs, id, data, parent

    def _get(
        self,
        classes: list[str],
        tags: list[str],
        attrs: list[str],
        id: list[str],
        data: list[str],
    ) -> list[Element]:
        return [
            e
            for e in self.elements
            if all([cls in str(e.attrs.get("class", "")).split(" ") for cls in classes])
            and all([tag == e for tag in tags])
            and all([attr in e.attrs.keys() for attr in attrs])
            and all([_id == str(e.attrs.get("id", "")) for _id in id])
            and all([_data == e.data for _data in data])
        ]

    def get(self, query: str) -> list[Element]:
        """
        .class_name
        #id_name
        tag_name
        [attribute]
        {data}
        (parent)
        """
        classes, tags, attrs, id, data, parent = self.parse_query(query)
        base_elements = self._get(classes, tags, attrs, id, data)
        while parent:
            possible_parents = self._get(
                parent[0], parent[1], parent[2], parent[3], parent[4]
            )
            for base_element in base_elements:
                found = False
                for possible_parent in possible_parents:
                    if base_element in possible_parent.inner_html:
                        found = True
                        break
                if not found:
                    base_elements.remove(base_element)
            parent = parent[-1]
        print(classes, tags, attrs, id, data)
        return base_elements

    def scrape(
        self, url: str | list[str], headers: MutableMapping[str, str] = {}
    ) -> HTTPError | None:
        if isinstance(url, list):
            "TODO: Multithreading"
        else:
            try:
                req = request.Request(url, headers=headers)
                with request.urlopen(req) as resp:
                    self.content = resp.read().decode("utf-8")
                self.feed(self.content)
            except HTTPError as e:
                return e
        return None
