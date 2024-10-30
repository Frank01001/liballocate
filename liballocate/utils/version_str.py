#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from __future__ import annotations

class VersionStr(str):
    """String that represents a version."""
    
    def __eq__(self: VersionStr, other: VersionStr) -> bool:
        return self == other

    def __ne__(self: VersionStr, other: VersionStr) -> bool:
        return self != other
    
    def __lt__(self: VersionStr, other: VersionStr) -> bool:
        this_numbers = [int(n) for n in self.split('.')]
        other_numbers = [int(n) for n in other.split('.')]

        for this, other in zip(this_numbers, other_numbers):
            if this < other:
                return True
            elif this > other:
                return False
            
        return False
    
    def __gt__(self: VersionStr, other: VersionStr) -> bool:
        this_numbers = [int(n) for n in self.split('.')]
        other_numbers = [int(n) for n in other.split('.')]

        for this, other in zip(this_numbers, other_numbers):
            if this > other:
                return True
            elif this < other:
                return False
            
        return False
    
    def __le__(self: VersionStr, other: VersionStr) -> bool:
        return self < other or self == other
    
    def __ge__(self: VersionStr, other: VersionStr) -> bool:
        return self > other or self == other