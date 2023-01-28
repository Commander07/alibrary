from __future__ import annotations

import zlib
from dataclasses import dataclass
from enum import Enum
from typing import Literal


def deflate(data: bytes, compresslevel: int = 9) -> bytes:
    compress = zlib.compressobj(
        compresslevel, zlib.DEFLATED, -zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, 0
    )
    deflated = compress.compress(data)
    deflated += compress.flush()
    return deflated


@dataclass
class Color:
    def to_bytes(self) -> bytes:
        pass


@dataclass
class RGB(Color):
    red: int
    green: int
    blue: int
    bit_depth: Literal[8, 16] = 8

    def to_bytes(self) -> bytes:
        return (
            self.red.to_bytes(self.bit_depth // 8, "big")
            + self.green.to_bytes(self.bit_depth // 8, "big")
            + self.blue.to_bytes(self.bit_depth // 8, "big")
        )


@dataclass
class RGBA(Color):
    red: int
    green: int
    blue: int
    alpha: int
    bit_depth: Literal[8, 16] = 8

    def to_bytes(self) -> bytes:
        return (
            self.red.to_bytes(self.bit_depth // 8, "big")
            + self.green.to_bytes(self.bit_depth // 8, "big")
            + self.blue.to_bytes(self.bit_depth // 8, "big")
            + self.alpha.to_bytes(self.bit_depth // 8, "big")
        )


@dataclass
class Y(Color):
    luma: int
    bit_depth: Literal[8, 16] = 8

    def to_bytes(self) -> bytes:
        return self.luma.to_bytes(self.bit_depth // 8, "big")


@dataclass
class YA(Color):
    luma: int
    alpha: int
    bit_depth: Literal[8, 16] = 8

    def to_bytes(self) -> bytes:
        return self.luma.to_bytes(self.bit_depth // 8, "big") + self.alpha.to_bytes(
            self.bit_depth // 8, "big"
        )


class ColorMode(Enum):
    Y = 0
    RGB = 2
    INDEX = 3
    YA = 4
    RGBA = 6
    AUTO = -1


class Format(Enum):
    PNG = 0


class MismatchedColors(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class MismatchedBitDepth(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class UnknownFormat(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@dataclass
class Image:
    data: list[list[Color]]
    color_mode: ColorMode = ColorMode.AUTO

    def __post_init__(self) -> None:
        if self.color_mode == ColorMode.AUTO:
            found_color = ""
        else:
            found_color = self.color_mode.name
        found_bit_depth = 0
        for row in self.data:
            for color in row:
                if not found_bit_depth:
                    found_bit_depth = color.bit_depth
                elif found_bit_depth != color.bit_depth:
                    raise MismatchedBitDepth(found_bit_depth, color.bit_depth)
                if not found_color:
                    found_color = color.__class__.__name__
                elif found_color != color.__class__.__name__:
                    raise MismatchedColors(found_color, color.__class__.__name__)
        self.bit_depth = found_bit_depth
        self.color_mode = ColorMode[found_color]

    def export(self, path: str, format: Format = Format.PNG) -> None:
        if format == Format.PNG:
            with open(path, "wb") as file:
                data = b"\x00" + b"\x00".join(
                    [b"".join([color.to_bytes() for color in row]) for row in self.data]
                )
                height = len(self.data)
                width = 0
                for row in self.data:
                    if len(row) > width:
                        width = len(row)
                ihdr_crc = zlib.crc32(
                    b"\x49\x48\x44\x52"
                    + width.to_bytes(4, "big")
                    + height.to_bytes(4, "big")
                    + self.bit_depth.to_bytes(1, "big")
                    + self.color_mode.value.to_bytes(1, "big")
                    + b"\x00\x00\x00"
                ).to_bytes(4, byteorder="big")
                _deflate = deflate(data)
                adler32 = zlib.adler32(data).to_bytes(4, byteorder="big")
                idat_crc = zlib.crc32(
                    b"\x49\x44\x41\x54\x08\xd7" + _deflate + adler32
                ).to_bytes(4, byteorder="big")
                idat_len = (17 + len(_deflate)).to_bytes(4, byteorder="big")
                file.write(
                    b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52"
                    + width.to_bytes(4, "big")
                    + height.to_bytes(4, "big")
                    + b"\x08\x02\x00\x00\x00"
                    + ihdr_crc
                    + idat_len
                    + b"\x49\x44\x41\x54\x08\xd7"
                    + _deflate
                    + adler32
                    + idat_crc
                    + b"\x00\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82"
                )
        else:
            raise UnknownFormat(format)
