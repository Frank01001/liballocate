#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdebug.liblog import liblog

from liballocate.allocators.allocator import Allocator
from liballocate.allocators.ptmalloc2.tcache import Tcache
from liballocate.data.memory_area import MemoryArea

if TYPE_CHECKING:
    from libdebug.debugger.debugger import Debugger
    from libdebug.state.thread_context import ThreadContext
    from libdebug.data.breakpoint import Breakpoint

    from liballocate.clibs.clib import Clib

def _malloc_initializer_callback(thread: ThreadContext, bp: Breakpoint) -> None:
    """Callback for the malloc breakpoint."""
    allocator = thread.debugger.heap

    allocator._setup_accessors()
    allocator._is_initialized = True

    bp.disable()

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
        libc_pages = debugger.maps.filter(self.clib.file_path)

        self.libc = MemoryArea(libc_pages)

        # Add heap memory area
        heap_page = debugger.maps.filter("[heap]")

        if not heap_page:
            liblog.liballocate("Heap is not initialized yet. Waiting for the first allocation.")
            self._is_initialized = False

            self._debugger.breakpoint(
                "malloc",
                callback=_malloc_initializer_callback,
                file=self.clib.file_path,
            )
        else:
            self._is_initialized = True
    
    @property
    def is_initialized(self: Ptmalloc2Allocator) -> bool:
        """Returns True if the allocator is initialized, False otherwise."""
        return self._is_initialized
    
    def _setup_accessors(self: Ptmalloc2Allocator) -> None:
        """Sets up the accessors for the allocator."""
        heap_page = self._debugger.maps.filter("[heap]")[0]
        
        self.heap_vmap = heap_page

        if self.libc.version >= "2.26":
            self.tcache = Tcache(self)
