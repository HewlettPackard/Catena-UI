# (C) Copyright 2017 Hewlett Packard Enterprise Development LP.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import subprocess

KEY_DIR = os.path.expanduser("~/.catena/keys")
TMP_DIR = os.path.expanduser("~/.catena/tmp")


def ensure_directory_exists(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


ensure_directory_exists(KEY_DIR)
ensure_directory_exists(TMP_DIR)


def create_ethereum_account(password):
    """Create an ethereum account and return the account address and data file. """

    pw_file_path = os.path.join(TMP_DIR, 'pw.txt')
    # TODO(?): What if multiple people create an account at the same time?
    # TODO(?): Change file permissions to make this safer

    try:
        with open(pw_file_path, 'w') as pw_file:
            pw_file.write(password)

        output = subprocess.check_output(['geth', 'account', 'new', '--password', pw_file_path, '--keystore', KEY_DIR])

        last_line = output.split('\n')[-2]  # Really it's the second last line, the last line is empty

        start = 'Address: {'
        end = '}'
        if last_line.startswith(start) and last_line.endswith(end):
            address = last_line[len(start):len(last_line) - len(end)]
        else:
            raise Exception("Unfamiliar output when calling geth to create an account. Output: {}".format(output))

        # Keyfile got created, now find it, in case we have more than one
        for fn in os.listdir(KEY_DIR):
            if fn.endswith(address):
                return (address, os.path.join(KEY_DIR, fn))

        raise Exception("Key file not found after creating an account")
    finally:
        if os.path.exists(pw_file_path):
            os.remove(pw_file_path)


def get_ethereum_account(address):
    for fn in os.listdir(KEY_DIR):
        if fn.endswith(address):
            with open(os.path.join(KEY_DIR, fn)) as account_file:
                return json.load(account_file)


def get_ethereum_addresses():
    addresses = []

    for fn in os.listdir(KEY_DIR):
        with open(os.path.join(KEY_DIR, fn)) as account_file:
            account_data = json.load(account_file)
            addresses.append(account_data['address'])

    return addresses
