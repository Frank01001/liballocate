#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from liballocate.utils.version_str import VersionStr

from pwn import ELF

class Clib:
    """Represents a C standard library."""

    def __init__(self: Clib, name: str, version: VersionStr, file_path: str) -> None:
        self.name = name
        self.version = version
        self.file_path = file_path

        self.pwnlib_elf = ELF(file_path, checksec=False)

        self.md5 = self.pwnlib_elf["md5"]
        self.sha1 = self.pwnlib_elf["sha1"]
        self.sha256 = self.pwnlib_elf["sha256"]
        self.sha512 = self.pwnlib_elf["sha512"]
        self.build_id = self.pwnlib_elf["buildid"]

    @property
    def allocator_type(self: Clib) -> str:
        raise NotImplementedError()
    
    @property
    def allocator_class(self: Clib) -> type:
        raise NotImplementedError()
    
    @property
    def version_str(self: Clib) -> str:
        raise NotImplementedError()