#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FastbinEntry:
    """Represents a fastbin entry."""

    address: int
    """The address of the fastbin entry."""

    next: FastbinEntry | None
    """The next fastbin entry."""

    next_value: int
    """The next fastbin entry address. Contains the value at the position of the next (processed by reveal_ptr if necessary) pointer regardless of validity."""

    raw_next: int
    """The raw next fastbin entry address. Contains the value at the position of the next pointer regardless of validity (no reveal_ptr)."""

    def has_next(self: FastbinEntry) -> bool:
        """Returns whether the fastbin entry has a next entry."""
        return self.next is not None
