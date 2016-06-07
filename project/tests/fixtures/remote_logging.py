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

import time

import pytest

from configuration import config
try:
    from modules.remote_logger.remote_logger import RemoteLogger, RemoteLoggerConfiguration


    def _current_time():
        """Return timestamp in microseconds, rounded to a second."""
        return int(round(time.time() * 1000, -3))


    @pytest.fixture(scope="module", autouse=True)
    def log_components(request):
        logged_components = getattr(request.module, "logged_components", None)
        from_date = _current_time()
        log_file_name = request.module.__name__.split(".")[-1]

        def fin():
            if config.CONFIG["remote_log_enabled"] and logged_components is not None:
                logger_config = RemoteLoggerConfiguration(
                    from_date=from_date,
                    to_date=_current_time(),
                    app_names=logged_components,
                    destination_directory=log_file_name
                )
                remote_logger = RemoteLogger(logger_config)
                remote_logger.log_to_file()

        request.addfinalizer(fin)


except ImportError:
    pass