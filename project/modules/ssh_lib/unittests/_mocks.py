#
# Copyright (c) 2016 Intel Corporation
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


class MockConfig:
    JUMP_HOSTNAME = "test-host"
    JUMP_KEY_DIRECTORY = "/tmp/dir"
    JUMP_KEY_FILENAME = "test_key"
    EXISTING_JUMP_KEY_PATH = os.path.join(JUMP_KEY_DIRECTORY, JUMP_KEY_FILENAME)
    JUMP_KEY_HOME_DIR = "~/tmp/test_key"
    ACCESS_TO_CORE_TAP_FROM_JUMP = False

    def __init__(self, jump_hostname=JUMP_HOSTNAME, jump_key_path=EXISTING_JUMP_KEY_PATH,
                 direct_access_from_jump=ACCESS_TO_CORE_TAP_FROM_JUMP):
        self.tap_domain = "test-domain"
        self.ng_jump_ip = jump_hostname
        self.ng_jump_key_path = jump_key_path
        self.ng_jump_user_with_kubectl_config = "test-username-admin"
        self.ng_jump_user = "test-username-centos"
        self.access_to_core_services_from_jump = direct_access_from_jump
        self.ng_socks_proxy_port = 123
        self.master_0_hostname = "test-master-0"



class MockSystemMethods:
    @classmethod
    def isfile(cls, file_path):
        if file_path == MockConfig.EXISTING_JUMP_KEY_PATH:
            return True
        elif file_path == os.path.expanduser(MockConfig.JUMP_KEY_HOME_DIR):
            return True
        return False

    @classmethod
    def exists(cls, path):
        if path == MockConfig.JUMP_KEY_DIRECTORY:
            return True
        return False