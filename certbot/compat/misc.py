"""
This compat modules handle various platform specific calls that do not fall into one
particular category.
"""
from __future__ import absolute_import

import select
import sys
import logging.handlers

from certbot.compat import os

try:
    from win32com.shell import shell as shellwin32  # pylint: disable=import-error
except ImportError:  # pragma: no cover
    shellwin32 = None  # type: ignore

from certbot import errors


class RotatingFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, *args, **kwargs):
        super(RotatingFileHandler, self).__init__(*args, **kwargs)

        if os.name == 'nt':
            self.rotator = self._windows_rotator

    def _windows_rotator(self, source, dest):
        if os.path.exists(source):
            # Certbot for Windows run exclusively on Python 3.x, so os.replace exists.
            os.replace(source, dest)


def raise_for_non_administrative_windows_rights():
    # type: () -> None
    """
    On Windows, raise if current shell does not have the administrative rights.
    Do nothing on Linux.

    :raises .errors.Error: If the current shell does not have administrative rights on Windows.

    """
    if shellwin32 and shellwin32.IsUserAnAdmin() == 0:
        raise errors.Error('Error, certbot must be run on a shell with administrative rights.')


def readline_with_timeout(timeout, prompt):
    # type: (float, str) -> str
    """
    Read user input to return the first line entered, or raise after specified timeout.

    :param float timeout: The timeout in seconds given to the user.
    :param str prompt: The prompt message to display to the user.

    :returns: The first line entered by the user.
    :rtype: str

    """
    try:
        # Linux specific
        #
        # Call to select can only be done like this on UNIX
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if not rlist:
            raise errors.Error(
                "Timed out waiting for answer to prompt '{0}'".format(prompt))
        return rlist[0].readline()
    except OSError:
        # Windows specific
        #
        # No way with select to make a timeout to the user input on Windows,
        # as select only supports socket in this case.
        # So no timeout on Windows for now.
        return sys.stdin.readline()


WINDOWS_DEFAULT_FOLDERS = {
    'config': 'C:\\Certbot',
    'work': 'C:\\Certbot\\lib',
    'logs': 'C:\\Certbot\\log',
}
LINUX_DEFAULT_FOLDERS = {
    'config': '/etc/letsencrypt',
    'work': '/var/lib/letsencrypt',
    'logs': '/var/log/letsencrypt',
}


def get_default_folder(folder_type):
    # type: (str) -> str
    """
    Return the relevant default folder for the current OS

    :param str folder_type: The type of folder to retrieve (config, work or logs)

    :returns: The relevant default folder.
    :rtype: str

    """
    try:
        # Linux specific
        import fcntl  # pylint: disable=import-error,unused-import,unused-variable
        return LINUX_DEFAULT_FOLDERS[folder_type]
    except ImportError:
        # Windows specific
        return WINDOWS_DEFAULT_FOLDERS[folder_type]


def underscores_for_unsupported_characters_in_path(path):
    # type: (str) -> str
    """
    Replace unsupported characters in path for current OS by underscores.
    :param str path: the path to normalize
    :return: the normalized path
    :rtype: str
    """
    if os.name != 'nt':
        # Linux specific
        return path

    # Windows specific
    drive, tail = os.path.splitdrive(path)
    return drive + tail.replace(':', '_')
