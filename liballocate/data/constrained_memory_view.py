#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from libdebug.debugger.debugger import Debugger


class ConstrainedMemoryView:
    """A memory interface for the target process, intended for direct memory access.

    Attributes:
            getter (Callable[[int, int], bytes]): A function that reads a variable amount of data from the target's memory.
            setter (Callable[[int, bytes], None]): A function that writes memory to the target process.
            align_to (int, optional): The address alignment that must be used when reading and writing memory. Defaults to 1.
    """

    def __init__(
        self: ConstrainedMemoryView,
        base: int,
        size: int,
        debugger: Debugger,
        align_to: int = 1,
    ) -> None:
        """Initializes the memory view with the given parameters.

        Args:
            base (int): The base address of the memory view.
            size (int): Size of the memory view.
            debugger (Debugger): The debugger to use.
            align_to (int, optional): The address alignment that must be used when reading and writing memory. Defaults to 1.
        """
        self.base = base
        self.size = size
        self.align_to = align_to
        self._debugger = debugger

    def __getitem__(self: ConstrainedMemoryView, index: object) -> bytes:
        d = self._debugger

        if isinstance(index, int):
            self._check_bounds(index)
            print(f"DEBUG: {self.base + index:#x}")
            
            return d.memory[self.base + index, "absolute"]

        # Handle two-element tuple indexing (e.g., [a, l])
        elif isinstance(index, tuple) and len(index) == 2:
            start, length = index
            
            self._check_bounds(start)
            self._check_bounds(start + length)

            print(f"DEBUG: {self.base + start:#x}, {length:#x}")
            return d.memory[self.base + start, length, "absolute"]

        # Handle slice indexing (e.g., [a:b])
        elif isinstance(index, slice):
            start = index.start
            stop = index.stop

            self._check_bounds(start)
            self._check_bounds(stop)
            print(f"DEBUG: {self.base + start:#x}, {self.base + stop:#x}")
            return d.memory[self.base + start:self.base + stop, "absolute"]
        else:
            raise TypeError("Invalid index type")
        
    def __setitem__(self: ConstrainedMemoryView, index: object, value: bytes) -> None:
        d = self._debugger

        if isinstance(index, int):
            self._check_bounds(index)
            
            d.memory[self.base + index, "absolute"] = value

        # Handle two-element tuple indexing (e.g., [a, l])
        elif isinstance(index, tuple) and len(index) == 2:
            start, length = index
            
            self._check_bounds(start)
            self._check_bounds(start + length)

            d.memory[self.base + start, length, "absolute"] = value

        # Handle slice indexing (e.g., [a:b])
        elif isinstance(index, slice):
            start = index.start
            stop = index.stop

            self._check_bounds(start)
            self._check_bounds(stop)
            
            d.memory[self.base + start:self.base + stop, "absolute"] = value
        else:
            raise TypeError("Invalid index type")
        
    def _check_bounds(self:ConstrainedMemoryView, address: int):
        if address < 0 or address > self.size:
            raise ValueError("Address out of bounds")