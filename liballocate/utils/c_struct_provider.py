#
# Copyright (c) 2024 Francesco Panebianco, Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from libdestruct.c.struct_parser import definition_to_type


class CStructProvider:
    """Provides C struct parsing and caching capabilities."""
    _instance = None

    def __new__(cls, *args, **kwargs) -> CStructProvider:
        if cls._instance is None:
            cls._instance = super(CStructProvider, cls).__new__(cls)
        return cls._instance

    def __init__(self: CStructProvider) -> None:
        self.parsed_structs = {}

    def has_cached_struct(self: CStructProvider, struct: str) -> bool:
        """Returns whether the given struct is cached or not

        Args:
            struct (str): The struct name.

        Returns:
            bool: True if the struct is cached, False otherwise.
        """
        return struct in self.parsed_structs.keys()

    def parse_struct(
        self: CStructProvider, struct: str, struct_definition: str
    ) -> type:
        """Parses the given struct if not cached and returns the struct type.

        Args:
            struct (str): The struct name.
            struct_definition (str): The struct definition.

        Returns:
            type: The libdestruct struct type.
        """
        if struct in self.parse_struct.keys():
            return self.parsed_structs[struct]

        struct_type = definition_to_type(struct_definition)

        self.parsed_structs[struct] = struct_type

        return struct_type
