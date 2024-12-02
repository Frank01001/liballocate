#
# Copyright (c) 2024 Francesco Panebianco, Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from typing import TYPE_CHECKING

from libdestruct import inflater

from liballocate.allocators.allocator import Allocator
from liballocate.utils.c_struct_provider import CStructProvider

if TYPE_CHECKING:
    from libdebug.debugger.debugger import Debugger

    from liballocate.clibs.clib import Clib


class CustomAllocator(Allocator):
    """Represents the custom allocator. Uses libdestruct to parse the struct definitions."""

    def __init__(self: CustomAllocator, libc: Clib) -> None:
        """Initializes the custom allocator."""
        super().__init__(libc)

        # perthread_definition = None
        # entry_definition = None

        # #TODO: Implement DWARF parsing of the struct definitions or decide a better way to get them
        # # Check if the struct is cached, otherwise find struct definition
        # if not c_struct_provider.has_cached_struct(tcache_pt_struct_name):
        #     # Get struct definitions from debuginfod
        #     dbg_elf = ELFFile(open(allocator.clib.debuginfod_path, "rb"))
        #     perthread_struct = ...
        #     entry_struct = ...

        #     perthread_definition = perthread_struct.data()
        #     entry_definition = entry_struct.data()

        # # If cached, the definition will be ignored
        # self._tcache_perthread_struct_t = c_struct_provider.parse_struct(
        #     tcache_pt_struct_name,
        #     perthread_definition,
        # )

        # self._tcache_entry_t = c_struct_provider.parse_struct(
        #     tcache_struct_name,
        #     entry_definition,
        # )

    # TODO: Implement the custom allocator
    def decorate_debugger(self: CustomAllocator, debugger: Debugger) -> None:
        """Decorates the given debugger with the custom interface.

        Args:
            debugger (Debugger): The debugger to decorate.
        """
        pass

    @property
    def is_initialized(self: CustomAllocator) -> bool:
        """Returns True if the allocator is initialized, False otherwise."""
        # TODO: Implement this method
