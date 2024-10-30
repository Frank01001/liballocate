#
# Copyright (c) 2024 Francesco Panebianco, Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

from libdestruct.c.struct_parser import definition_to_type


class CStructProvider:
    _instance = None

    def __new__(cls, *args, **kwargs) -> CStructProvider:
        if cls._instance is None:
            cls._instance = super(CStructProvider, cls).__new__(cls)
        return cls._instance

    def __init__(self: CStructProvider) -> None:
        self.parsed_structs = {}

    def parse_struct(
        self: CStructProvider, struct: str, struct_definition: str
    ) -> type:
        if struct in self.parse_struct.keys():
            return self.parse_struct[struct]

        struct_type = definition_to_type(struct_definition)

        self.parsed_structs[struct] = struct_type

        return struct_type
