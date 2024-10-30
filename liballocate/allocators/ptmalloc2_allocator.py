#
# Copyright (c) 2023-2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from liballocate.allocators.allocator import Allocator
from liballocate.data.memory_area import MemoryArea
from libdebug.data.memory_map import MemoryMap

if TYPE_CHECKING:
    from liballocate.clibs.clib import Clib
    from libdebug.debugger.debugger import Debugger

class Ptmalloc2Allocator(Allocator):
    """Represents the ptmalloc2 allocator."""
    def __init__(self: Ptmalloc2Allocator, libc: Clib) -> None:
        """Initializes the ptmalloc2 allocator."""
        super().__init__(libc)

    def decorate_debugger(self: Ptmalloc2Allocator, debugger: Debugger) -> None:
        """Decorates the given debugger with the ptmalloc2 interface.

        Args:
            debugger (Debugger): The debugger to decorate.
        """
        super().decorate_debugger(debugger)

        # Add libc memory area
        libc_pages = debugger.maps.filter("libc.so")

        self.libc = MemoryArea(libc_pages)

        # Add heap memory area
        heap_page = debugger.maps.filter("[heap]")[0]

        self.heap_vmap = heap_page

    @property
    def tcache(self: Ptmalloc2Allocator) -> MemoryMap:
        """Returns the tcache memory map."""
        return self.libc.data
    
    @property
    def main_arena(self: Ptmalloc2Allocator) -> MemoryMap:
        """Returns the main arena memory map."""
        return self.libc.text
    
    @property
    def fastbins(self: Ptmalloc2Allocator) -> MemoryMap:
        """Returns the fastbins memory map."""
        return self.libc.data