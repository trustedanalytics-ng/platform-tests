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
import logging
from contextlib import contextmanager

import config

logger = logging.getLogger(__name__)


class UserNamePool:
    def __init__(self):
        self.is_occupied = {name: False for name in config.perf_user_names}
        self.lock = logging.threading.Lock()
        self._USE_DEFAULT_NAME = len(self.is_occupied) == 0

    def lock_name(self) -> str:
        if self._USE_DEFAULT_NAME:
            name = config.admin_username
        else:
            name = None
            while name is None:
                with self.lock:
                    name = self._next_available_name()
                    self.is_occupied[name] = True
        return name

    def unlock_name(self, name: str):
        if name in self.is_occupied:
            with self.lock:
                self.is_occupied[name] = False
        else:
            logger.warning('Name not in pool: {}'.format(name))

    def _next_available_name(self):
        return next((name for name, occupied in self.is_occupied.items() if not occupied), None)

username_pool = UserNamePool()


class UsernameLock:
    def __enter__(self):
        self.name = username_pool.lock_name()
        return self.name

    def __exit__(self, exc_type, exc_val, exc_tb):
        username_pool.unlock_name(self.name)
