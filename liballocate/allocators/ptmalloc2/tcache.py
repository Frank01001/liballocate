#
# Copyright (c) 2023-2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from liballocate.utils.c_structs import ptmalloc2_tcache_entry, ptmalloc2_tcache_perthread_struct
from libdestruct.c.struct_parser import definition_to_type

from libdestruct import inflater

if TYPE_CHECKING:
    from liballocate.clibs.glibc import Glibc
    from liballocate.allocators.ptmalloc2.ptmalloc2_allocator import Ptmalloc2Allocator

class Tcache:
    """Represents the ptmalloc2 tcache implementation."""
    def __init__(self: Tcache, allocator: Ptmalloc2Allocator) -> None:
        """Initializes the tcache with the given GNU C Library.

        Args:
            libc (Glibc): The GNU C Library to use with the tcache.
        """

        if allocator.libc.version >= "2.31":
            tcache_entry_definition = ptmalloc2_tcache_entry
            tcache_perthread_struct_definition = ptmalloc2_tcache_perthread_struct
        
        self.do_ptr_mangling = allocator.libc.version >= "2.32"

        struct_inflater = inflater(allocator._debugger.memory)