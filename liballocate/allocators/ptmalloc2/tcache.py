#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from liballocate.allocators.ptmalloc2.tcache_entry import TcacheEntry

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

        # Tcache chunk address
        # TODO: This is only valid in the single-threaded case
        # We should get this value dynamically
        self.tcache_ptr = allocator.heap_vmap.base + 0x10

        # TODO: Implement tunable fetch
        self.TCACHE_MAX_BINS = 64
        self.TCACHE_FILL_COUNT = 7

    @property
    def has_tcache_key(self) -> bool:
        """Returns whether the tcache has a key or not."""
        return self._allocator_ref._libc.version >= "2.29"
    

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

        memory = self._allocator_ref._debugger.memory

        #  typedef struct tcache_perthread_struct
        # {
        # char counts[TCACHE_MAX_BINS];
        # tcache_entry *entries[TCACHE_MAX_BINS];
        # } tcache_perthread_struct;

        tcache_counts_base = self.tcache_ptr + 0x10
        tcache_entries_base = tcache_counts_base + self.TCACHE_MAX_BINS

        # Get the address of the head tcache entry
        curr_address = tcache_entries_base + tcache_index * 0x8

        num_entries = int.from_bytes(
            memory[
                tcache_counts_base + tcache_index : tcache_counts_base
                + tcache_index
                + 1,
                "absolute",
            ]
        )
        curr_entry = None
        counter = 0

        # Unwind the tcache linked list
        while curr_address is not None and counter < num_entries:
            next_address = memory[curr_address : curr_address + 8, "absolute"]
            next_address = int.from_bytes(next_address, byteorder="little")

            # Get the next tcache entry address
            if self._allocator_ref.has_protect_ptr:
                # typedef struct tcache_entry
                # {
                #     struct tcache_entry *next;
                #     /* This field exists to detect double frees.  */
                #     uintptr_t key;
                # } tcache_entry;
                plain_next_address = self._allocator_ref.reveal_ptr(
                    curr_address,
                    next_address,
                )
            else:
                plain_next_address = curr_address

            # Get the key if present
            if self.has_tcache_key:
                key = int.from_bytes(
                    memory[curr_address + 0x8 : curr_address + 0x10, "absolute"],
                    byteorder="little",
                )
            else:
                key = None

            # Check if the next tcache entry is valid
            is_next_valid = True

            try:
                _ = memory[plain_next_address, 1, "absolute"]
            except MemoryError:
                is_next_valid = False

            processed_next_address = plain_next_address if is_next_valid else None

            # Create the tcache entry
            entry = TcacheEntry(
                address=curr_address,
                next=None,
                next_value=next_address,
                raw_next=plain_next_address,
                _key=key,
            )

            # Link the tcache entries
            if curr_entry is not None:
                curr_entry.next = entry

            # Update the current entry and address
            curr_entry = entry
            curr_address = processed_next_address

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

        memory = self._allocator_ref._debugger.memory

        tcache_counts_base = self.tcache_ptr + 0x10
        tcache_entries_base = tcache_counts_base + self.TCACHE_MAX_BINS

        # Replace the head tcache entry
        curr_address = tcache_entries_base + tcache_index * 0x8

        # Get the next tcache entry address
        if self._allocator_ref.has_protect_ptrect_ptr:
            cypher_next_address = self._allocator_ref.reveal_ptr(
                curr_address,
                value,
            )
        else:
            cypher_next_address = value

        memory[curr_address : curr_address + 8, "absolute"] = (
            cypher_next_address.to_bytes(8, byteorder="little")
        )

        # Unwind the tcache linked list to count the number of entries
        count = 0

        # Unwind the tcache linked list to count the number of entries
        while curr_address is not None:
            next_address = (
                int.from_bytes(
                    memory[curr_address : curr_address + 8, "absolute"],
                    byteorder="little",
                ),
            )

            # Get the next tcache entry address
            if self._allocator_ref.has_protect_ptrect_ptr:
                plain_next_address = self._allocator_ref.reveal_ptr(
                    curr_address,
                    next_address,
                )
            else:
                plain_next_address = next_address

            # Check if the next tcache entry is valid
            is_next_valid = True

            try:
                _ = memory[plain_next_address, 1, "absolute"]
            except MemoryError:
                is_next_valid = False

            next_address = plain_next_address if is_next_valid else None

            # Update the current address
            curr_address = next_address

            # Increment the count
            count += 1

        # Set the head tcache entry count
        count = min(max(count, 1), self.TCACHE_FILL_COUNT)
        count_bytes = count.to_bytes(1, byteorder="little")

        memory[
            tcache_counts_base + tcache_index : tcache_counts_base + tcache_index + 1,
            "absolute",
        ] = count_bytes
