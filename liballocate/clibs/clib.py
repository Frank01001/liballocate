#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

import hashlib

from elftools.elf.elffile import ELFFile
from libdebug.utils.elf_utils import _debuginfod

from liballocate.utils.version_str import VersionStr


class Clib:
    """Represents a C standard library."""

    def __init__(self: Clib, name: str, version: VersionStr, file_path: str) -> None:
        self.name = name
        self.version = version
        self.file_path = file_path

        clib_file = open(file_path, "rb")
        clib_contents = clib_file.read()

        clib_elf = ELFFile(clib_file)

        # Compute hashes
        self.md5 = hashlib.md5(clib_contents).hexdigest()
        self.sha1 = hashlib.sha1(clib_contents).hexdigest()
        self.sha256 = hashlib.sha256(clib_contents).hexdigest()
        self.sha512 = hashlib.sha512(clib_contents).hexdigest()
        self.build_id = clib_elf.get_section_by_name(".note.gnu.build-id").data()[16:]
        
        self.elfclass = clib_elf.elfclass
        self.endianness = "little" if clib_elf.little_endian else "big"

        # Hexlify the build_id
        self.build_id = "".join("{:02x}".format(byte) for byte in self.build_id)

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

    @property
    def common_name(self: Clib) -> str:
        raise NotImplementedError()

    def __repr__(self: Clib) -> str:
        return f"{self.version_str} | Allocator: {self.allocator_type}"
