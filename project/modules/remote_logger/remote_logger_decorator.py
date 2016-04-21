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

from datetime import datetime
from inspect import isclass
from time import mktime

from .remote_logger_configuration import RemoteLoggerConfiguration
from .remote_logger import RemoteLogger
from .config import Config


class RemoteLoggerDecorator(object):
    TEAR_DOWN_METHOD = "tearDownClass"

    def __init__(self, *args):
        self.__components = args
        self.__from_date = self.__date()
        self.__name = None

    def __call__(self, cls):
        self.__name = cls.__name__
        if not isclass(cls):
            raise TypeError("Remote logger decorator should be used on a class.")
        if cls.components and not self.__components:
            self.__components = cls.components
        if not self.__components:
            raise RemoteLoggerDecoratorMissingComponentsException()
        if Config.is_remote_logger_enabled():
            self.__add_tear_down_class_decorator(cls)
        return cls

    def __add_tear_down_class_decorator(self, cls):
        """Add log decorator to tear down class method."""
        tear_down_class_method = getattr(cls, self.TEAR_DOWN_METHOD, None)
        if not callable(tear_down_class_method):
            raise RemoteLoggerDecoratorMissingMethodException(self.TEAR_DOWN_METHOD)
        cls.tearDownClass = self.__log(cls.tearDownClass)

    def __log(self, func):
        """Run remote logger after given function call."""

        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            finally:
                remote_logger = RemoteLogger(self.__create_configuration())
                remote_logger.log_to_file()

        return wrapped

    def __create_configuration(self):
        """Create configuration for remote logger."""
        return RemoteLoggerConfiguration(
            from_date=self.__from_date,
            to_date=self.__date(),
            app_names=self.__components,
            destination_directory=self.__name
        )

    @staticmethod
    def __date():
        """Return the current datetime in seconds."""
        t = datetime.now()
        return int(round(mktime(t.timetuple()) + 1e-6 * t.microsecond) * 1000)


class RemoteLoggerDecoratorMissingMethodException(Exception):
    TEMPLATE = "Method '{}' is missing."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))


class RemoteLoggerDecoratorMissingComponentsException(Exception):
    def __init__(self):
        super().__init__("You need to specify at least one component to get logs from.")


log_components = RemoteLoggerDecorator
