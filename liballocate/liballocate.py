#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from libdebug.debugger.debugger import Debugger
from libdebug.liblog import liblog

from liballocate.clibs.clib_identifier import identify_clib
from liballocate.liblog.liblog_decoration import decorate_liblog
from liballocate.utils.resolve_clib_utilities import resolve_clib_from_binary


def activate(debugger: Debugger, clib_name: str = None) -> None:
    """Activates liballocate's interface to the allocator on the given debugger.

    Args:
        debugger (Debugger): The libdebug debugger object to use with liballocate.
        clib_name (str, optional): The name of the C library used by the debugger. If not provided, liballocate will attempt to identify the C library automatically. Defaults to None.
    """
    decorate_liblog(liblog)
    liblog.liballocate("Activating liballocate on the debugger.")

    # Identify the C library used by the debugger
    path_to_binary = debugger._internal_debugger._process_full_path

    clib_name, clib_pathname = resolve_clib_from_binary(path_to_binary, clib_name)

    clib = identify_clib(clib_name, clib_pathname)

    liblog.liballocate(f"Identified C library: {clib_name} at {clib_pathname}\n\n{clib}")

    # Check if the debugger is already using liballocate
    if not hasattr(debugger, "active_extensions"):
        debugger.active_extensions = ["liballocate"]
    elif "liballocate" not in debugger.active_extensions:
        debugger.active_extensions.append("liballocate")
    else:
        raise ValueError("liballocate is already active on the debugger.")
