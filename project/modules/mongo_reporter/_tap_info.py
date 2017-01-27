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
import config
from modules.tap_logger import get_logger
from modules.tap_object_model.platform_info import PlatformInfo

logger = get_logger(__name__)


class TapInfo(object):

    @classmethod
    def get_build_number(cls):
        if config.tap_build_number:
            return config.tap_build_number
        else:
            return cls._retrieve_build_number_from_platform()

    @classmethod
    def _retrieve_build_number_from_platform(cls):
        try:
            platform_info = PlatformInfo.get()
            build_number = cls._build_number_from_platform_version(platform_info.platform_version)
        except Exception as e:
            logger.warning("Couldn't retrieve TAP build number from TAP.\nException: {}".format(e))
            build_number = config.tap_build_number

        return build_number

    @classmethod
    def _build_number_from_platform_version(cls, platform_version):
        return int(platform_version.split(".")[-1])
