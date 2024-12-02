#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdebug.liblog import liblog

from liballocate.allocators.ptmalloc2.fastbin_entry import FastbinEntry

if TYPE_CHECKING:
    from liballocate.allocators.ptmalloc2.ptmalloc2_allocator import Ptmalloc2Allocator


class Fastbin:
    """Represents the ptmalloc2 fastbin implementation."""

    def __init__(self: Fastbin, allocator: Ptmalloc2Allocator) -> None:
        """Initializes the fastbin with the given GNU C Library.

        Args:
            libc (Glibc): The GNU C Library to use with the fastbin.
        """
        self._allocator_ref = allocator

        match allocator._debugger.arch:
            case "amd64" | "aarch64":
                INTERNAL_SIZE_T = 8
            case "i386":
                INTERNAL_SIZE_T = 4
            case _:
                INTERNAL_SIZE_T = 4
                liblog.liballocate(
                    f"Unsupported architecture: {allocator._debugger.arch}. INTERNAL_SIZE_T will default to 32-bit."
                )

        self.SIZE_SZ = INTERNAL_SIZE_T
        self.NFASTBINS = 10
        self.MAX_FAST_SIZE = 80 * INTERNAL_SIZE_T // 4

    def _fastbin_index(self: Fastbin, size: int) -> int:
        """Returns the fastbin index of the given size.

        Args:
            size (int): The size of the fastbin entry.

        Returns:
            int: The fastbin index.
        """
        return (size >> (4 if self.SIZE_SZ == 8 else 3)) - 2

    def _get_fastbinY_by_index(self: Fastbin, index: int) -> FastbinEntry:
        """Returns the head fastbin entry of the given size or None if the fastbin entry is not found.

        Args:
            index (int): The index of the fastbin entry.

        Returns:
            FastbinEntry: The head fastbin entry.
        """
        return self._allocator_ref.main_arena.fastbinsY[index].value

    def __getitem__(self: Fastbin, size: int) -> FastbinEntry:
        """Returns the head fastbin entry of the given size or None if the fastbin entry is not found.

        Args:
            size (int): The size of the fastbin entry.

        Returns:
            FastbinEntry: The head fastbin entry.
        """
        
        index = self._fastbin_index(size)
        curr_fastbin_head_addr = self._get_fastbinY_by_index(index)

        valid_next = True
        curr_entry = None

        d = self._allocator_ref._debugger
        arch_word_size = self._allocator_ref.clib.elfclass // 8

        while valid_next:
            address = curr_fastbin_head_addr
            raw_next = d.memory[address, arch_word_size, "absolute"]

            if self._allocator_ref.has_protect_ptr:
                next_value = self._allocator_ref.reveal_ptr(address, raw_next)
            else:
                next_value = raw_next

            # Create entry
            new_entry = FastbinEntry(address, None, next_value, raw_next)

            if curr_entry is not None:
                curr_entry.next = new_entry
            
            curr_entry = new_entry
            curr_fastbin_head_addr = next_value

            # Check if the next fastbin entry is valid
            try:
                _ = d.memory[curr_fastbin_head_addr, 1, "absolute"]
            except MemoryError:
                valid_next = False

        return curr_entry

