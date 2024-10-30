#
# Copyright (c) 2023-2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from liballocate.clibs.clib import Clib
from libdebug.debugger.debugger import Debugger

class Allocator:
    """Represents an allocator implementation."""
    def __init__(self: Allocator, clib: Clib) -> None:
        """Initializes the allocator with the given C library.
        
        Args:
            clib (Clib): The C library to use with the allocator.
        """
        self.clib = clib

    def decorate_debugger(self: Allocator, debugger: Debugger) -> None:
        """Decorates the given debugger with the allocator's symbols.
        
        Args:
            debugger (Debugger): The debugger to decorate.
        """
        # Add the heap attribute to the debugger.
        debugger.__setattr__("heap", self)