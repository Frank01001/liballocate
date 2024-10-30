#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

import hashlib

from libdebug.utils.elf_utils import _debuginfod

from liballocate.utils.elf_info import get_build_id
from liballocate.utils.version_str import VersionStr


class Clib:
    """Represents a C standard library."""

    def __init__(self: Clib, name: str, version: VersionStr, file_path: str) -> None:
        self.name = name
        self.version = version
        self.file_path = file_path

        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()

        elf_header = file_content[:0x40]

        if file_content[:4] != b"\x7fELF":
            raise ValueError("Not a valid ELF file.")

        # Determine if the ELF file is 32-bit or 64-bit
        self.word_size = 8 if (elf_header[4] == 2) else 4

        # Determine endianness
        self.endianness = "little" if file_content[5] == 1 else "big"

        target_abi = elf_header[7]
        abi_version = elf_header[8]

        if target_abi != 3 or abi_version != 0:
            raise ValueError(
                "Unsupported ABI. Currently only System V Linux ABI is supported."
            )

        e_machine = elf_header[0x12:0x14]

        match e_machine:
            case b"\x03\x00":
                self.arch = "i386"
            case b"\x3e\x00":
                self.arch = "amd64"
            case b"\x3e\x00":
                self.arch = "aarch64"
            case _:
                raise ValueError(
                    "Unsupported architecture. Stick to libdebug supported architectures."
                )

        # Resolve Build ID
        self.build_id = get_build_id(file_content)

        # Compute hashes
        self.md5 = hashlib.md5(file_content).hexdigest()
        self.sha1 = hashlib.sha1(file_content).hexdigest()
        self.sha256 = hashlib.sha256(file_content).hexdigest()
        self.sha512 = hashlib.sha512(file_content).hexdigest()

        # Retrieve debug information
        self.debuginfod_path = _debuginfod(self.build_id)

    @property
    def allocator_type(self: Clib) -> str:
        raise NotImplementedError()

    @property
    def allocator_class(self: Clib) -> type:
        raise NotImplementedError()

    @property
    def version_str(self: Clib) -> str:
        raise NotImplementedError()
