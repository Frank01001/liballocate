#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from liballocate.allocators.ptmalloc2.ptmalloc2_allocator import Ptmalloc2Allocator
from liballocate.clibs.clib import Clib

if TYPE_CHECKING:
    from liballocate.utils.version_str import VersionStr


class Glibc(Clib):
    """Represents the GNU C Library."""

    def __init__(self: Glibc, version: VersionStr, file_path: str) -> None:
        super().__init__("glibc", version, file_path)

    @property
    def allocator_type(self: Glibc) -> str:
        """Returns the allocator type name for the GNU C Library."""
        return "ptmalloc2"

    @property
    def allocator_class(self: Glibc) -> type:
        """Returns the allocator class for the GNU C Library."""
        return Ptmalloc2Allocator

    @property
    def version_str(self: Glibc) -> str:
        """Returns the version string for the GNU C Library."""
        return f"glibc-{self.version}"
    
    @property
    def common_name(self: Glibc) -> str:
        """Returns the common name for the GNU C Library."""
        return "libc"
