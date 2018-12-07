#!/usr/bin/env python
"""Merges multiple Python requirements files into one file.

Requirements files specified later take precedence over earlier ones. Only
simple SomeProject==1.2.3 format is currently supported.

"""

from __future__ import print_function

import sys
import re
import os


REQUIREMENT_PATTERN = r'^([\w\-\[\],\.]+)((?:[=<>!~]{1,2}[^,]+(?:,|))+)$'


def read_file(file_path):
    """Reads in a Python requirements file.

    :param str file_path: path to requirements file

    :returns: mapping from a project to its pinned version
    :rtype: dict

    """
    with open(file_path) as file:
        lines = file.readlines()

    data = {}
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            search = re.search(REQUIREMENT_PATTERN, line.strip())
            if search:
                project = search.group(1)
                versions = search.group(2)
                data[project] = versions
            else:
                raise ValueError("Unexpected syntax '{0}'".format(line.strip()))

    return data


def output_requirements(requirements):
    """Prepare print requirements to stdout.

    :param dict requirements: mapping from a project to its pinned version

    """
    return os.linesep.join('{0}{1}'.format(k, v)
                           for k, v in sorted(requirements.items()))


def main(*files):
    """Merges multiple requirements files together and prints the result.

    Requirement files specified later in the list take precedence over earlier
    files.

    :param tuple files: paths to requirements files

    """
    data = {}
    for file_path in files:
        data.update(read_file(file_path))
    return output_requirements(data)


if __name__ == '__main__':
    merged_requirements = main(*sys.argv[1:])
    print(merged_requirements)
