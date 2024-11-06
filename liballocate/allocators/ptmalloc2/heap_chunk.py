#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from libdebug.debugger.debugger import Debugger

class Ptmalloc2Chunk:
    """Represents a ptmalloc2 chunk."""

    def __init__(self: Ptmalloc2Chunk, address: int, debugger: Debugger):
        """
        Initializes a Ptmalloc2Chunk instance given a debugger and an address.
        
        :param address: Address of the chunk's content as returned by malloc().
        :param debugger: A Debugger object to access memory values.
        """
        self._address = address
        self._debugger = debugger

        # Read chunk metadata from memory
        try:
            chunk_metadata = self._debugger.memory[address - 0x10, 0x10, "absolute"]
        except Exception as e:
            raise ValueError(f"Cannot read chunk metadata from address {address}: {e}")

        # Extract chunk metadata
        self._prev_size = int.from_bytes(chunk_metadata[0:8], byteorder="little")
        size_plus_flags = int.from_bytes(chunk_metadata[8:16], byteorder="little")

        self._size = size_plus_flags & 0xfffffffffffffff8
        self._is_allocated_arena = size_plus_flags & 0x2 == 0x2
        self._is_mmapped = size_plus_flags & 0x2 == 0x2
        self._is_prev_inuse = size_plus_flags & 0x1 == 0x1

        # Extract chunk content
        self._content = self._debugger.memory[address, self._size - 0x10, "absolute"]

    @property
    def address(self: Ptmalloc2Chunk) -> int:
        return self._address

    @property
    def size(self: Ptmalloc2Chunk) -> int:
        return self._size

    @size.setter
    def size(self: Ptmalloc2Chunk, value: int):
        self._size = value
        self._update_size_in_memory()

    # Prev_size property
    @property
    def prev_size(self) -> int:
        return self._prev_size

    @prev_size.setter
    def prev_size(self: Ptmalloc2Chunk, value: int):
        self._prev_size = value
        self._update_prev_size_in_memory()

    # Is_allocated_arena property
    @property
    def is_allocated_arena(self) -> bool:
        return self._is_allocated_arena

    @is_allocated_arena.setter
    def is_allocated_arena(self: Ptmalloc2Chunk, value: bool):
        self._is_allocated_arena = value
        self._update_flags_in_memory()

    # Is_mmapped property
    @property
    def is_mmapped(self) -> bool:
        return self._is_mmapped

    @is_mmapped.setter
    def is_mmapped(self: Ptmalloc2Chunk, value: bool):
        self._is_mmapped = value
        self._update_flags_in_memory()

    # Is_prev_inuse property
    @property
    def is_prev_inuse(self) -> bool:
        return self._is_prev_inuse

    @is_prev_inuse.setter
    def is_prev_inuse(self: Ptmalloc2Chunk, value: bool):
        self._is_prev_inuse = value
        self._update_flags_in_memory()

    # Content property
    @property
    def content(self) -> bytes:
        return self._content

    @content.setter
    def content(self: Ptmalloc2Chunk, value: bytes):
        self._content = value
        self._update_content_in_memory()

    # Methods to update values in memory
    def _update_size_in_memory(self):
        """Updates the chunk's size in memory."""
        size_plus_flags = self._compute_size_plus_flags()
        self._debugger.memory[self._address - 0x8, 0x8, "absolute"] = size_plus_flags.to_bytes(8, "little")

    def _update_prev_size_in_memory(self):
        """Updates the previous chunk size in memory."""
        self._debugger.memory[self._address - 0x10, 0x8, "absolute"] = self._prev_size.to_bytes(8, "little")

    def _update_flags_in_memory(self):
        """Updates the flags in memory."""
        size_plus_flags = self._compute_size_plus_flags()
        self._debugger.memory[self._address - 0x8, 0x8, "absolute"] = size_plus_flags.to_bytes(8, "little")

    def _update_content_in_memory(self):
        """Updates the content of the chunk in memory."""
        self._debugger.memory[self._address, len(self._content), "absolute"] = self._content

    def _compute_size_plus_flags(self) -> int:
        """Helper method to recompute size with flags."""
        size_plus_flags = self._size
        if self._is_allocated_arena:
            size_plus_flags |= 0x2
        if self._is_mmapped:
            size_plus_flags |= 0x2
        if self._is_prev_inuse:
            size_plus_flags |= 0x1
        return size_plus_flags
