#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct import inflater
from elftools.elf.elffile import ELFFile
from liballocate.utils.c_struct_provider import CStructProvider

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
        c_struct_provider = CStructProvider()

        # Inflate memory with libdestruct
        struct_inflater = inflater(allocator._debugger.memory)

        # Put glibc version before the struct name for caching
        tcache_pt_struct_name = allocator.clib.version_str + "_tcache_perthread_struct"
        tcache_struct_name = allocator.clib.version_str + "_tcache_entry"

        perthread_definition = None
        entry_definition = None

        # Check if the struct is cached, otherwise find struct definition
        if not c_struct_provider.has_cached_struct(tcache_pt_struct_name):
            # Get struct definitions from debuginfod
            dbg_elf = ELFFile(open(allocator.clib.debuginfod_path, "rb"))
            perthread_struct = dbg_elf.get_section_by_name("tcache_perthread_struct")
            entry_struct = dbg_elf.get_section_by_name("tcache_entry")
        
            perthread_definition = perthread_struct.data()
            entry_definition = entry_struct.data()

        # If cached, the definition will be ignored
        self._tcache_perthread_struct_t = c_struct_provider.parse_struct(
            tcache_pt_struct_name,
            perthread_definition,
        )

        self._tcache_entry_t = c_struct_provider.parse_struct(
            tcache_struct_name,
            entry_definition,
        )

        # Tcache chunk address
        # TODO: This is only valid in the single-threaded case
        # We should get this value dynamically
        self.tcache_ptr = allocator.heap_vmap.base + 0x10

        # Inflate the tcache perthread struct
        self._perthread_struct = struct_inflater.inflate(
            self._tcache_perthread_struct_t, 
            self.tcache_ptr
        )

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