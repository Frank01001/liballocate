#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from dataclasses import dataclass

@dataclass
class UnsortedBinEntry:
    """Represents the ptmalloc2 unsorted bin entry implementation."""

    next: UnsortedBinEntry | None
    """The next unsorted bin entry."""

    prev: UnsortedBinEntry | None
    """The previous unsorted bin entry."""

    fk: int
    """The forward link pointer."""

    bk: int
    """The backward link pointer."""

    @property
    def raw_next(self: UnsortedBinEntry) -> int:
        """Returns the raw next unsorted bin entry address. Alias for fk."""
        return self.fk

    @property
    def raw_prev(self: UnsortedBinEntry) -> int:
        """Returns the raw previous unsorted bin entry address. Alias for bk."""
        return self.bk
