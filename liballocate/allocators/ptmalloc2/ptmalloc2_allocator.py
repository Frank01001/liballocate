#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct import inflater
from libdebug.liblog import liblog

from liballocate.allocators.allocator import Allocator
from liballocate.allocators.ptmalloc2.chunk_accessor import Ptmalloc2ChunkAccessor
from liballocate.allocators.ptmalloc2.constants import MALLOC_STATE_STRUCT
from liballocate.allocators.ptmalloc2.tcache import Tcache
from liballocate.utils.c_struct_provider import c_struct_provider

if TYPE_CHECKING:
    from libdebug.debugger.debugger import Debugger

    from liballocate.clibs.clib import Clib


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

        self._is_initialized = False

        if self._is_heap_initialized_in_libc():
            # We can already initialize the allocator
            self._setup_accessors()
            self._is_initialized = True

    @property
    def is_initialized(self: Ptmalloc2Allocator) -> bool:
        """Returns True if the allocator is initialized, False otherwise."""
        # Lazy check
        if not self._is_initialized:
            if not self._is_heap_initialized_in_libc():
                return False
            else:
                self._setup_accessors()
                self._is_initialized = True

        return True

    def _setup_accessors(self: Ptmalloc2Allocator) -> None:
        """Sets up the accessors for the allocator."""
        heap_page = self._debugger.maps.filter("heap")[0]

        # TODO: This could be an old instance of the [heap] page, if brk() was called then the mapping will be different
        # Should we perform filter at each access?
        self.heap_vmap = heap_page

        # If cached, the definition will be ignored
        self.MallocState = c_struct_provider.parse_struct(
            "malloc_state",
            MALLOC_STATE_STRUCT,
        )

        libdestruct = inflater(self._debugger.memory)

        loc_main_arena = self._debugger.symbols.filter("main_arena")

        # Initialize the main arena
        self.main_arena = libdestruct.inflate(self.MallocState, loc_main_arena)

        # Accessor to retrieve chunks
        self.chunk_at = Ptmalloc2ChunkAccessor(self._debugger)

        if self.clib.version >= "2.26":
            self.tcache = Tcache(self)

    # TODO: This looks a bit like spaghetti code, we should refactor this eventually
    # Trying to get any attribute of the object will trigger the initialization
    # or an error if the heap is not initialized
    def __getattr__(self, name):
        # Get the value of the attribute without recursion
        is_initialized = self.__getattribute__("is_initialized")

        # Allowed before initialization of the heap
        allowed_attributes = ["clib"]

        if not is_initialized and name not in allowed_attributes:
            liblog.liballocate(
                "The ptmalloc2 allocator is not initialized. "
                "Please ensure that the target process is running and the allocator is in use."
            )
            return None

        return super().__getattr__(name)

    def protect_ptr(self: Tcache, pos: int, ptr: int) -> int:
        """Implements PROTECT_PTR.

        Args:
            pos (int): The position of the pointer.
            ptr (int): The pointer to protect.

        Returns:
            int: The protected pointer.
        """
        return (pos >> 12) ^ ptr

    def reveal_ptr(self: Tcache, pos: int, ptr: int) -> int:
        """Alias for protect_ptr.

        Args:
            pos_ptr (int): The position of the pointer.
            ptr (int): The pointer to protect.
        """
        return self.protect_ptr(pos, ptr)

    # TODO: There could be security backports that implement this feature
    # Find a better way to check for this feature in the future
    @property
    def has_protect_ptr(self) -> bool:
        """Returns whether the tcache has pointer mangling or not."""
        return self._allocator_ref._libc.version >= "2.32"

    def _is_heap_initialized_in_libc(self: Ptmalloc2Allocator) -> bool:
        """Returns whether the heap is initialized or not."""
        return len(self._debugger.maps.filter("[heap]")) > 0
