#
# Copyright (c) 2024 Francesco Panebianco, Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from elftools.elf.elffile import ELFFile
from libdestruct import inflater

from liballocate.allocators.ptmalloc2.tcache_entry import TcacheEntry
from liballocate.utils.c_struct_provider import CStructProvider

if TYPE_CHECKING:
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
        self._struct_inflater = inflater(allocator._debugger.memory)

        # Put glibc version before the struct name for caching
        tcache_pt_struct_name = allocator.clib.version_str + "_tcache_perthread_struct"
        tcache_struct_name = allocator.clib.version_str + "_tcache_entry"

        perthread_definition = None
        entry_definition = None

        #TODO: Implement DWARF parsing of the struct definitions or decide a better way to get them
        # Check if the struct is cached, otherwise find struct definition
        if not c_struct_provider.has_cached_struct(tcache_pt_struct_name):
            # Get struct definitions from debuginfod
            dbg_elf = ELFFile(open(allocator.clib.debuginfod_path, "rb"))
            perthread_struct = ...
            entry_struct = ...

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
        self._perthread_struct = self._struct_inflater.inflate(
            self._tcache_perthread_struct_t, self.tcache_ptr
        )

    @property
    def has_tcache_key(self) -> bool:
        """Returns whether the tcache has a key or not."""
        return self._allocator_ref._libc.version >= "2.29"

    # TODO: There could be security backports that implement this feature
    # Find a better way to check for this feature in the future
    @property
    def has_protect_ptr(self) -> bool:
        """Returns whether the tcache has pointer mangling or not."""
        return self._allocator_ref._libc.version >= "2.32"

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

    # define csize2tidx(x) (((x) - MINSIZE + MALLOC_ALIGNMENT - 1) / MALLOC_ALIGNMENT)
    @staticmethod
    def _csize2tidx(size: int) -> int:
        """Returns the tcache index for the given size.

        Args:
            size (int): The size to convert.

        Returns:
            int: The tcache index.
        """
        return (size - 0x10 + 0x10 - 1) // 0x10

    def __getitem__(self: Tcache, size: int) -> TcacheEntry:
        """Returns the head tcache entry of the given size or None if the tcache entry is not found.

        Args:
            size (int): The size of the tcache entry.

        Returns:
            TcacheEntry: The head tcache entry at the given size.
        """
        if size < 0x10:
            raise ValueError(f"Invalid size: {hex(size)} is smaller than 0x10")

        # Get the tcache index for the given size
        tcache_index = self._csize2tidx(size)

        # Get the address of the head tcache entry
        curr_address = self._perthread_struct.entries[tcache_index].value
        num_entries = self._perthread_struct.counts[tcache_index]
        curr_entry = None
        counter = 0

        # Unwind the tcache linked list
        while curr_address is not None and counter < num_entries:
            # Handle struct from memory
            entry_struct = self._struct_inflater.inflate(
                self._tcache_entry_t,
                curr_address,
            )

            # Get the next tcache entry address
            if self.has_protect_ptr:
                plain_next_address = self.reveal_ptr(
                    entry_struct.next.address,
                    entry_struct.next.value,
                )
            else:
                plain_next_address = entry_struct.next.value

            # Check if the next tcache entry is valid
            is_next_valid = True

            try:
                self._allocator_ref._debugger.memory.read(plain_next_address, 1)
            except:
                is_next_valid = False

            # Get the key if present
            key = None if not self.has_tcache_key else entry_struct.key.value

            next_address = plain_next_address if is_next_valid else None

            # Create the tcache entry
            entry = TcacheEntry(curr_address, next_address, key)

            # Link the tcache entries
            if curr_entry is not None:
                curr_entry.next = entry

            # Update the current entry and address
            curr_entry = entry
            curr_address = next_address

            # Increment the counter
            counter += 1

    def __setitem__(self: Tcache, size: int, value: int) -> None:
        """Sets the head tcache entry of the given size. If the tcache entry has count to 0 or invalid, it will be set to 1.

        Args:
            size (int): The size of the tcache entry.
            value (int): The address of the tcache entry.
        """
        # Get the tcache index for the given size
        tcache_index = self._csize2tidx(size)

        # Unwind the tcache linked list to count the number of entries
        count = 0

        curr_address = value

        # Unwind the tcache linked list
        while curr_address is not None:
            # Handle struct from memory
            entry_struct = self._struct_inflater.inflate(
                self._tcache_entry_t,
                curr_address,
            )

            # Get the next tcache entry address
            if self.has_protect_ptr:
                plain_next_address = self.reveal_ptr(
                    entry_struct.next.address,
                    entry_struct.next.value,
                )
            else:
                plain_next_address = entry_struct.next.value

            # Check if the next tcache entry is valid
            is_next_valid = True

            try:
                self._allocator_ref._debugger.memory.read(plain_next_address, 1)
            except:
                is_next_valid = False

            next_address = plain_next_address if is_next_valid else None

            # Update the current address
            curr_address = next_address

            # Increment the count
            count += 1

        # Set the head tcache entry count
        self._perthread_struct.counts[tcache_index] = count if count > 0 else 1

        if self.has_protect_ptr:
            pos = self._perthread_struct.entries[tcache_index].address

            # Encode the pointer
            encoded_ptr = self.protect_ptr(pos, value)
        else:
            encoded_ptr = value
        
        # Set the head tcache entry address
        self._perthread_struct.entries[tcache_index].value = encoded_ptr
