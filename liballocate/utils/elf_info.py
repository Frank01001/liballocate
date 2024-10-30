#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

import hashlib
import struct
from typing import Tuple


class ELFInfo:
    """Extract information from an ELF file."""

    def __init__(self: ELFInfo, filepath: str, compute_hashes: bool = True, parse_dynlibs: bool = True):
        """Initialize the ELFInfo object with the given ELF file.

        Args:
            filepath (str): Path to the ELF file
            compute_hashes (bool): Whether to compute hashes of the ELF file
            parse_dynlibs (bool): Whether to parse dynamic libraries from the ELF file
        """
        self.filename = filepath
        self.is_64_bit = None
        self.endian = None
        self.header = {}
        self.program_headers = []
        self.dynamic_libraries = []
        self.data = self._read_file_content()

        if not self._is_elf():
            raise ValueError(f"{filepath} is not a valid ELF file.")

        # Parse the ELF header
        self._parse_elf_header()

        # Determine the architecture based on the machine type
        match self.header["machine"]:
            case 0x03:
                self.arch = "i386"
            case 0x3E:
                self.arch = "amd64"
            case 0xB7:
                self.arch = "aarch64"
            case _:
                raise ValueError(
                    "Unsupported architecture. Stick to libdebug supported architectures."
                )

        # Parse other relevant information
        if parse_dynlibs:
            self._parse_program_headers()
            self._extract_dynamic_libraries()

        if compute_hashes:
            self._calculate_hashes()
            self.build_id = self._compute_build_id()

    def _read_file_content(self: ELFInfo):
        """Read the entire content of the ELF file at once."""
        with open(self.filename, "rb") as f:
            return f.read()

    def _is_elf(self: ELFInfo):
        """Check if the file is an ELF file."""
        magic = self.data[:4]
        return magic == b"\x7fELF"

    def _parse_elf_header(self: ELFInfo):
        """Parse the ELF header and store relevant properties."""
        e_ident = self.data[:16]
        self.is_64_bit = e_ident[4] == 2
        self.endian = "little" if e_ident[5] == 1 else "big"

        elf_header_format = self.endian + (
            "HHIQQQIHHHHHH" if self.is_64_bit else "HHIIIIIHHHHHH"
        )
        elf_header_size = struct.calcsize(elf_header_format)
        elf_header_data = struct.unpack(elf_header_format, self.data[0:elf_header_size])

        # Populate the ELF header dictionary with relevant properties
        keys = [
            "type",
            "machine",
            "version",
            "entry",
            "phoff",
            "shoff",
            "flags",
            "ehsize",
            "phentsize",
            "phnum",
            "shentsize",
            "shnum",
            "shstrndx",
        ]
        self.header = dict(zip(keys, elf_header_data))

    def _parse_program_headers(self: ELFInfo):
        """Parse program headers to determine if it's dynamically linked."""
        phoff = self.header["phoff"]
        phnum = self.header["phnum"]
        phentsize = self.header["phentsize"]

        phdr_format = self.endian + ("IIQQQQQQ" if self.is_64_bit else "IIIIIIII")
        phdr_size = struct.calcsize(phdr_format)

        for i in range(phnum):
            phdr_start = phoff + i * phdr_size
            phdr = struct.unpack(
                phdr_format, self.data[phdr_start : phdr_start + phdr_size]
            )
            self.program_headers.append(phdr)

    def _extract_dynamic_libraries(self: ELFInfo):
        """Extract dynamic libraries from the ELF's dynamic section."""
        for phdr in self.program_headers:
            if phdr[0] == 2:  # PT_DYNAMIC
                dyn_offset = phdr[2] if self.is_64_bit else phdr[1]
                dyn_size = phdr[5] if self.is_64_bit else phdr[4]

                dyn_entry_format = self.endian + ("QQ" if self.is_64_bit else "II")
                dyn_entry_size = struct.calcsize(dyn_entry_format)

                # Read the dynamic segment entries
                while True:
                    dyn_entry_start = dyn_offset
                    dyn_entry = struct.unpack(
                        dyn_entry_format,
                        self.data[dyn_entry_start : dyn_entry_start + dyn_entry_size],
                    )
                    if dyn_entry[0] == 1:  # DT_NEEDED
                        lib_offset = dyn_entry[1]
                        # Read the library name from the string table
                        lib_name = self._read_string(dyn_offset + lib_offset)
                        self.dynamic_libraries.append(lib_name)
                    elif dyn_entry[0] == 0:  # DT_NULL, end of dynamic segment
                        break
                    dyn_offset += dyn_entry_size

    def _read_string(self: ELFInfo, offset: int):
        """Read a null-terminated string from the ELF data at a specific offset."""
        start = offset
        while self.data[start] != 0:
            start += 1
        return self.data[offset:start].decode()

    def _calculate_hashes(self: ELFInfo):
        """Calculate hash values of the ELF file."""
        self.md5 = hashlib.md5(self.data).hexdigest()
        self.sha1 = hashlib.sha1(self.data).hexdigest()
        self.sha256 = hashlib.sha256(self.data).hexdigest()
        self.sha512 = hashlib.sha512(self.data).hexdigest()

    def _compute_build_id(self: ELFInfo):
        """
        Extract the GNU Build ID from an ELF binary without using external libraries.

        Args:
            binary_data: Raw bytes of the ELF binary

        Returns:
            Optional[bytes]: The build ID as bytes, or None if not found
        """
        try:
            # Get string table location
            strtab_offset, strtab_size = self._get_string_table()

            # Read number of section headers
            if self.is_64_bit:
                num_sections = struct.unpack("<H", self.data[60:62])[0]
            else:
                num_sections = struct.unpack("<H", self.data[48:50])[0]

            # Iterate through section headers
            for i in range(num_sections):
                section_offset = self.header["shoff"] + (i * self.header["shentsize"])
                name_idx, sh_type, sh_offset, sh_size = self._read_section_header(
                    section_offset
                )

                # Get section name from string table
                if name_idx >= strtab_size:
                    continue

                name_end = self.data[
                    strtab_offset + name_idx : strtab_offset + strtab_size
                ].find(b"\x00")
                name = self.data[
                    strtab_offset + name_idx : strtab_offset + name_idx + name_end
                ]

                # Check if this is the build-id section
                if name == b".note.gnu.build-id":
                    note_data = self.data[sh_offset : sh_offset + sh_size]

                    # Parse note section
                    namesz = struct.unpack("<I", note_data[0:4])[0]
                    descsz = struct.unpack("<I", note_data[4:8])[0]
                    note_type = struct.unpack("<I", note_data[8:12])[0]

                    # Check if it's a build-id note (type 3)
                    if note_type == 3:
                        # Skip name padding
                        name_padding = (4 - (namesz % 4)) % 4
                        desc_offset = 12 + namesz + name_padding

                        # Return the build-id
                        return note_data[desc_offset : desc_offset + descsz]

            return None

        except Exception as e:
            raise ValueError(f"Failed to parse Build ID: {str(e)}")

    def _get_string_table(self: ELFInfo) -> Tuple[int, int]:
        """
        Find and return the string table offset and size
        """
        # Read section header string table index
        if self.is_64_bit:
            strtab_idx = struct.unpack("<H", self.data[62:64])[0]
        else:
            strtab_idx = struct.unpack("<H", self.data[50:52])[0]

        # Get string table section header
        str_hdr_offset = self.header["shoff"] + (strtab_idx * self.header["shentsize"])
        _, _, strtab_offset, strtab_size = self._read_section_header(str_hdr_offset)

        return strtab_offset, strtab_size

    def _read_section_header(self: ELFInfo, offset: int) -> Tuple[int, int, int, int]:
        """
        Read section header and return name offset, type, offset and size
        """
        if self.is_64_bit:
            name_idx = struct.unpack("<I", self.data[offset : offset + 4])[0]
            sh_type = struct.unpack("<I", self.data[offset + 4 : offset + 8])[0]
            sh_offset = struct.unpack("<Q", self.data[offset + 24 : offset + 32])[0]
            sh_size = struct.unpack("<Q", self.data[offset + 32 : offset + 40])[0]
        else:
            name_idx = struct.unpack("<I", self.data[offset : offset + 4])[0]
            sh_type = struct.unpack("<I", self.data[offset + 4 : offset + 8])[0]
            sh_offset = struct.unpack("<I", self.data[offset + 16 : offset + 20])[0]
            sh_size = struct.unpack("<I", self.data[offset + 20 : offset + 24])[0]

        return name_idx, sh_type, sh_offset, sh_size

    def __str__(self: ELFInfo):
        return (
            f"ELF Info for {self.filename}\n"
            f"Architecture: {'64-bit' if self.is_64_bit else '32-bit'}\n"
            f"Endian: {'Little' if self.endian == '<' else 'Big'}\n"
            f"ELF Header: {self.header}\n"
            f"Program Headers: {self.program_headers}\n"
            f"Dynamic Libraries: {self.dynamic_libraries}\n"
            f"Hashes:\n"
            f"  MD5: {self.hashes['md5']}\n"
            f"  SHA-1: {self.hashes['sha1']}\n"
            f"  SHA-256: {self.hashes['sha256']}\n"
            f"  SHA-512: {self.hashes['sha512']}"
            f"Build ID: {self.build_id}"
        )
