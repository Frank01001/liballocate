#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TcacheEntry:
    """Represents a tcache entry."""

    address: int
    """The address of the tcache entry."""

    next: TcacheEntry | None
    """The next tcache entry."""

    _key: int | None = None
    """The key of the tcache entry."""

    @property
    def key(self: TcacheEntry) -> int:
        """Returns the key of the tcache entry."""
        if self._key is None:
            raise NotImplementedError("Tcache key not present in glibc version.")

        return self._key

    def has_next(self: TcacheEntry) -> bool:
        """Returns whether the tcache entry has a next entry."""
        return self.next is not None
