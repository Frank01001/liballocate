#
# This file is part of libdebug Python library (https://github.com/libdebug/libdebug).
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from setuptools import find_packages, setup

setup(
    name="liballocate",
    version="0.1.0",
    author="Frank01001",
    description="A libdebug extension for the dynamic allocator",
    packages=find_packages(include=["liballocate", "liballocate.*"]),
    install_requires=["libdebug", "pwntools", "libdestruct"],
)
