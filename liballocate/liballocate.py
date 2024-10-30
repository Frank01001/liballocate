#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from typing import TYPE_CHECKING

from liballocate.clib_identifier import identify_clib
from liballocate.utils.elf_info import ELFInfo

if TYPE_CHECKING:
    from libdebug.debugger.debugger import Debugger


def activate(debugger: Debugger) -> None:
    """Activates liballocate's interface to the allocator on the given debugger.

    Args:
        debugger (Debugger): The libdebug debugger object to use with liballocate.
    """

    # Check if the debugger is already using liballocate
    if not hasattr(debugger, "active_extensions"):
        debugger.active_extensions = ["liballocate"]
    elif "liballocate" not in debugger.active_extensions:
        debugger.active_extensions.append("liballocate")
    else:
        raise ValueError("liballocate is already active on the given debugger.")

    # Identify the C library used by the debugger
    path_to_binary = debugger._internal_debugger._process_full_path

    binary = ELFInfo(path_to_binary, compute_hashes=False, parse_dynlibs=True)

    # Test
    print(binary)
