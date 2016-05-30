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

import base64
import functools
import random
import string

from modules.http_calls import kubernetes_broker


@functools.total_ordering
class KubernetesSecret(object):
    comparable_attributes = ["org_guid", "key_id", "username", "password"]

    def __init__(self, org_guid, key_id, username, password):
        self.org_guid = org_guid
        self.key_id = key_id
        self.username = username
        self.password = password

    def __eq__(self, other):
        return all((getattr(self, a) == getattr(other, a) for a in self.comparable_attributes))

    def __lt__(self, other):
        return self.key_id < other.key_id

    def __repr__(self):
        return "{} (key_id={})".format(self.__class__.__name__, self.key_id)

    def __hash__(self):
        return hash(tuple(getattr(self, a) for a in self.comparable_attributes))

    @staticmethod
    def generate_key(key_len=20):
        base = string.digits
        return "".join([random.choice(base) for _ in range(key_len)])

    @staticmethod
    def generate_random_string(length=20):
        base = string.ascii_letters
        return "".join([random.choice(base) for _ in range(length)])

    @staticmethod
    def _encode_string_for_request(request_string):
        return base64.b64encode(bytes(request_string, "utf-8"))

    @staticmethod
    def _decode_string_from_response(response_string):
        return base64.b64decode(response_string.encode()).decode("utf-8")

    @classmethod
    def create(cls, org_guid, key_id=None, username=None, password=None):
        if key_id is None:
            key_id = cls.generate_key()
        if username is None:
            username = cls.generate_random_string()
        if password is None:
            password = cls.generate_random_string()
        kubernetes_broker.k8s_broker_create_secret(org_guid=org_guid, key_id=key_id,
                                                   username_b64=cls._encode_string_for_request(username),
                                                   password_b64=cls._encode_string_for_request(password))
        return cls(org_guid=org_guid, key_id=key_id, username=username, password=password)

    @classmethod
    def get(cls, org_guid, key_id):
        response = kubernetes_broker.k8s_broker_get_secret(org_guid=org_guid, key_id=key_id)
        username = cls._decode_string_from_response(response["data"]["username"])
        password = cls._decode_string_from_response(response["data"]["password"])
        secret = cls(org_guid=org_guid, key_id=response["metadata"]["name"], username=username, password=password)
        return secret

    def update(self, new_username=None, new_password=None):
        if new_username is not None:
            self.username = new_username
            new_username = self._encode_string_for_request(new_username)
        else:
            new_username = self._encode_string_for_request(self.username)
        if new_password is not None:
            self.password = new_password
            new_password = self._encode_string_for_request(new_password)
        else:
            new_password = self._encode_string_for_request(self.password)
        kubernetes_broker.k8s_broker_update_secret(org_guid=self.org_guid, key_id=self.key_id,
                                                   username_b64=new_username, password_b64=new_password)

    def delete(self):
        kubernetes_broker.k8s_broker_delete_secret(org_guid=self.org_guid, key_id=self.key_id)