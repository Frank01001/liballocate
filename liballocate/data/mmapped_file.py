#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from elftools.elf.elffile import ELFFile
from libdebug.debugger.debugger import Debugger

from liballocate.data.constrained_memory_view import ConstrainedMemoryView


class MmappedFile(ConstrainedMemoryView):
    """Represents a memory-mapped file."""

    def __init__(self: MmappedFile, debugger: Debugger, file_path: str) -> None:
        """Initializes the memory-mapped file with the given debugger and file

        Args:
            debugger (Debugger): The debugger to use.
            file_path (str): The file path to map.
        """
        self._debugger = debugger
        self._file_path = file_path

        self.elf = ELFFile(open(file_path, "rb"))

        file_maps = self._debugger.maps.filter(file_path)
        file_base = file_maps[0].start
        file_size = file_maps[-1].end - file_base

        # Allow access to the entire file
        super().__init__(file_base, file_size, debugger)

        # For all ELF sections, expose an accessor with the same name
        for section in self.elf.iter_sections():
            # Skip empty sections
            if section.name == "":
                continue

            # Make the accessor name a valid Python identifier
            accessor_name = section.name

            if accessor_name.startswith("."):
                accessor_name = accessor_name[1:]

            accessor_name = accessor_name.replace(".", "_")

            # Create a memory view for the section
            new_mem_view = ConstrainedMemoryView(
                file_base + section.header.sh_addr,
                section.header.sh_size,
                debugger,
            )

            setattr(self, accessor_name, new_mem_view)
