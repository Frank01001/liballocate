#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from liballocate.clibs.clib import Clib
from liballocate.clibs.glibc import Glibc


def identify_clib(file_path: str) -> Clib:
    with open(file_path, "rb") as file:
        content = file.read()

    # Check if it is the GNU C Library
    glibc_ver_index = (
        content.find(b"GNU C Library (GNU libc) stable release version") + 48
    )

    # Pattern: GNU C Library (GNU libc) stable release version X.XX
    if glibc_ver_index != -1:
        # Nearest space after the version string
        window = content[glibc_ver_index : glibc_ver_index + 10]

        end_of_version_str = glibc_ver_index + window.find(b"\n") - 1
        version_str = content[glibc_ver_index:end_of_version_str].decode("utf-8")

        return Glibc(version_str, file_path)
    else:
        raise NotImplementedError(
            "The C library is not among available implementations :( ."
        )
