#
# Copyright (c) 2016 - 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import re
import sys

SEARCH_PATTERN = re.compile(r'# Copyright \(c\) ([-0-9\s\,]*) Intel Corporation')

HEADERS = [
"""#
# Copyright (c) {{date_ranges}} Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
""",
]

def check_file_headers(root_path, extensions, path_exceptions):
    """Checks if all files under the given root_path with the given extensions have proper license
    headers.

    Args:
        root_path (str): Path in which headers will be scanned. Will scan all subdirectories
            recursively.
        extensions (set[str]): Only the files with one of theese extensions (eg. "py") will be
            scanned.
        path_exceptions (list[str]): Which paths not to scan.
    Returns:
        bool: True if all scanned files have proper licenses. False otherwise.
    """
    path_regexes = ['(?:^{})'.format(path) for path in path_exceptions]
    regex = re.compile('|'.join(path_regexes))

    bad_paths = []
    for path, _, file_names in os.walk(root_path):
        if regex.match(path):
            continue

        filtered_files = [file_name for file_name in file_names
                          if os.path.splitext(file_name)[1] in extensions]

        for file_path in [os.path.join(path, file_name) for file_name in filtered_files]:
            result = check_license_header(file_path)
            if result != True:
                bad_paths.append(result)
    if bad_paths:
        print('Wrong header in files: \n {}'.format("\n".join(bad_paths)))
        return False
    return True

def check_license_header(path):
    """Checks if a given file has proper license.

    This functions tries all the available headers. If at least one of the header
    matches, then function will True.

    Args:
        path: path to the file to be checked

    Returns:
        True if file has proper header, path to file otherwise
    """
    for header in HEADERS:
        if is_header_correct(path, header) is True:
            return True

    return path

def is_header_correct(path, header):
    """Compares single header against file

    Args:
        path: path to file to check
        header: header as a string

    Returns:
        True if header is correct, false otherwise

    Caveats:
        Short header will crash the tool
    """
    with open(path) as f:
        header = header.splitlines()
        # The first line can be a single '#' or '#!/usr/bin/env python3.4'
        # In case of the laster omit such line
        line = f.readline().strip()
        if len(line) > 1:
            line = f.readline().strip()

        if header[0] != line:
            print("File: " + path + " differs: " + header[0] + " != " + line)
            return False
        header = header[1:]

        # Second line is special...
        line = f.readline().strip()

        m = SEARCH_PATTERN.search(line)
        if m is None:
            print("File: " + path + " has improper year format: " + line)
            return False
        # But we do not compare it yet...
        header = header[1:]

        # Compare the rest
        for h in header:
            line = f.readline().strip()
            if h != line:
                print("File: " + path + " differs: " + header[0] + " != " + line)
                return False

    return True

if __name__ == '__main__':
    path_exceptions = ['./' + path for path in sys.argv[1].split(',')]
    extensions = {'.' + extension for extension in sys.argv[2].split(',')}

    if not check_file_headers('.', extensions, path_exceptions):
        sys.exit(1)
