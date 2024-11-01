#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct import inflater

if TYPE_CHECKING:
    from liballocate.clibs.glibc import Glibc
    from liballocate.allocators.ptmalloc2.ptmalloc2_allocator import Ptmalloc2Allocator

class Tcache:
    """Represents the ptmalloc2 tcache implementation."""
    def __init__(self: Tcache, allocator: Ptmalloc2Allocator) -> None:
        """Initializes the tcache with the given GNU C Library.

        Args:
            libc (Glibc): The GNU C Library to use with the tcache.
        """
        self._allocator_ref = allocator

        # struct_inflater = inflater(allocator._debugger.memory)

    @property
    def has_tcache_key(self) -> bool:
        """Returns whether the tcache has a key or not."""
        return self._allocator_ref._libc.version >= '2.29'
    
    @property
    def has_protect_ptr(self) -> bool:
        """Returns whether the tcache has pointer mangling or not."""
        return self._allocator_ref._libc.version >= '2.32'

    def protect_ptr(self: Tcache, pos: int, ptr: int) -> int:
        """Implements PROTECT_PTR.

        Args:
            pos (int): The position of the pointer.
            ptr (int): The pointer to protect.

        Returns:
            int: The protected pointer.
        """
        return ((pos >> 12) ^ ptr)
    
    def reveal_ptr(self: Tcache, pos: int, ptr: int) -> int:
        """Alias for protect_ptr.

        Args:
            pos_ptr (int): The position of the pointer.
            ptr (int): The pointer to protect.
        """
        return self.protect_ptr(pos, ptr)