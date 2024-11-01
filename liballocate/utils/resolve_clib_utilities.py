#
# Copyright (c) 2024 Francesco Panebianco, Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import os
from re import findall

from elftools.elf.elffile import ELFFile


def resolve_clib_from_binary(
    path_to_binary: str, clib_name: str = None
) -> tuple[str, str]:
    """Resolve the C library used by the debugger from the binary.

    Args:
        path_to_binary (str): The path to the binary used by the debugger.
        clib_name (str, optional): The name of the C library used by the debugger. If not provided, liballocate will attempt to identify the C library automatically. Defaults to None.

    Returns:
        str, str: The name and path of the C library used by the debugger.
    """
    binary = ELFFile(open(path_to_binary, "rb"))

    # Get list of dynamic libraries
    dynamic_section = binary.get_section_by_name(".dynamic")

    if not dynamic_section:
        raise NotImplementedError(
            "The binary is statically linked. liballocate does not support statically linked binaries yet."
        )

    # Extract DT_NEEDED entries which list required shared libraries
    libraries = [
        tag.needed
        for tag in dynamic_section.iter_tags()
        if tag.entry.d_tag == "DT_NEEDED"
    ]

    if clib_name is None:
        subset = [lib for lib in libraries if "libc" in lib]

        if not subset:
            raise ValueError(
                "The C library used by the debugger could not be identified automatically. Please specify the C library name manually."
            )
        elif len(subset) > 1:
            # Try exact match
            subset = [lib for lib in subset if lib == "libc.so.6"]

            if not subset:
                # Regex for libc-<version>.so
                subset = [lib for lib in subset if findall(r"libc-\d+\.\d+\.so", lib)]

                if not subset:
                    raise ValueError(
                        "The C library used by the debugger could not be identified automatically. Please specify the C library name manually."
                    )
            elif len(subset) > 1:
                raise ValueError(
                    "Multiple C libraries found in the binary. Please specify the C library name manually."
                )

            clib_name = subset[0]

    rpath = None
    runpath = None
    # Iterate over the dynamic tags to find DT_NEEDED for libc.so.6 and paths
    for tag in dynamic_section.iter_tags():
        if tag.entry.d_tag == "DT_RPATH":
            rpath = tag.val  # DT_RPATH path value
        elif tag.entry.d_tag == "DT_RUNPATH":
            runpath = tag.val  # DT_RUNPATH path value

    if rpath:
        clib_path = rpath
    elif runpath:
        clib_path = runpath
    elif os.environ.get("LD_LIBRARY_PATH"):
        clib_path = os.environ.get("LD_LIBRARY_PATH")
    elif os.environ.get("LD_PRELOAD") and "libc" in os.environ.get("LD_PRELOAD"):
        clib_path = os.environ.get("LD_PRELOAD")
    else:
        clib_path = "/usr/lib"

    clib_pathname = os.path.join(clib_path, clib_name)

    return clib_name, clib_pathname
