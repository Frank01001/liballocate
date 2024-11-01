#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from libdebug.data.memory_map_list import MemoryMapList
from libdebug.liblog import liblog

class MemoryArea:
    """Represents a memory region made of different pages for the same file."""

    def __init__(self: MemoryArea, pages: MemoryMapList) -> None:
        """Initializes the memory area."""
        self.pages = pages
        self.backing_file = pages[0].backing_file
        
        rx_pages = []
        rw_pages = []
        r_pages = []

        # Check if all pages are contiguous
        pages.sort(key=lambda x: x.start)

        for i in range(1, len(pages)):
            if pages[i-1].end != pages[i].start:
                raise ValueError(f"Memory area {self.backing_file} has non-contiguous pages.")

        # Resolve permissions of the pages
        for page in pages:
            if "r" in page.permissions and "x" in page.permissions:
                rx_pages.append(page)
            elif "r" in page.permissions and "w" in page.permissions:
                rw_pages.append(page)
            elif "r" in page.permissions:
                r_pages.append(page)
        
        # Save start and end of the area
        self.start = pages[0].start
        self.end = pages[-1].end

        # Save the text page
        if len(rx_pages) > 1:
            liblog.warning(f"Memory area {self.backing_file} has multiple x pages. Text will refer to the first one.")
        elif len(rx_pages) == 0:
            raise ValueError(f"Memory area {self.backing_file} has no x pages.")

        self.text = rx_pages[0]

        # Save the data / bss page
        if len(rw_pages) > 1:
            liblog.warning(f"Memory area {self.backing_file} has multiple rw pages. Data will refer to the first one.")
        elif len(rw_pages) == 0:
            raise ValueError(f"Memory area {self.backing_file} has no rw pages.")
        
        self.data = rw_pages[0]

        # Save the rodata page
        if len(r_pages) > 1:
            liblog.warning(f"Memory area {self.backing_file} has multiple r pages. Data will refer to the first one.")
        elif len(r_pages) == 0:
            raise ValueError(f"Memory area {self.backing_file} has no r pages.")
        
        self.rodata = r_pages[0]

    @property
    def base_address(self: MemoryArea) -> int:
        """Alias for start."""
        return self.start