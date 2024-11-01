#
# Copyright (c) 2024 Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from libdebug.liblog import LibLog
from types import MethodType
from libdebug.utils.ansi_escape_codes import ANSIColors

def _liballocate(self: LibLog, message: str, *args: str, **kwargs: str) -> None:
    """Log an error message to the general logger.

    Args:
        message (str): the message to log.
        *args: positional arguments to pass to the logger.
        **kwargs: keyword arguments to pass to the logger.
    """
    header = f"[{ANSIColors.CYAN}LIBALLOCATE{ANSIColors.DEFAULT_COLOR}]"
    self.general_logger.info(f"{header} {message}", *args, **kwargs)

def decorate_liblog(log_instance: LibLog) -> None:
    """Decorates the liblog module with additional functionality."""
    # Attach `liballocate` as a method to `log_instance`
    log_instance.liballocate = MethodType(_liballocate, log_instance)