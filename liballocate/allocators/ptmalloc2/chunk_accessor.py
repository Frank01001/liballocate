#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from libdebug.debugger.debugger import Debugger

from liballocate.allocators.ptmalloc2.heap_chunk import Ptmalloc2Chunk


class Ptmalloc2ChunkAccessor:
    """Used to return ptmalloc2 chunk objects given a chunk address."""

    def __init__(self: Ptmalloc2ChunkAccessor, debugger: Debugger) -> None:
        """Initializes the ptmalloc2 chunk accessor."""
        self._debugger = debugger

    def __getitem__(self: Ptmalloc2ChunkAccessor, address: int) -> Ptmalloc2Chunk:
        """Returns the ptmalloc2 chunk at the given address."""
        return Ptmalloc2Chunk(address, self._debugger)
