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

from .tap_object_model import Application, ServiceInstance
from .tap_logger import step
from tests.fixtures.assertions import assert_in_with_retry


class ApplicationStackValidator(object):
    def __init__(self, service: ServiceInstance):
        self.__validate_property("name", service.name)
        self.__validate_property("guid", service.id)
        self.__service = service
        self.__application = None
        self.__application_bindings = {}

    @property
    def application(self):
        """Application created and started for given service."""
        return self.__application

    @property
    def application_bindings(self):
        """Service bindings created for given application."""
        return self.__application_bindings

    def validate(self, expected_bindings=None, validate_application=True):
        """Validate service instance."""
        self._validate_instance_created()
        if validate_application:
            self._validate_application_created()
        if expected_bindings:
            self._validate_application_bound(expected_bindings)

    def validate_removed(self):
        """Validate that service instance and all its bindings have been properly removed."""
        self._validate_instance_has_been_removed()
        self._validate_application_has_been_removed()
        self._validate_bindings_have_been_removed()

    def _validate_instance_created(self):
        """Check if service instance has been properly created."""
        step("Check that service instance has been created")
        assert_in_with_retry(self.__service, ServiceInstance.get_list)

    def _validate_application_created(self):
        """Check if application for service instance has been properly created and started."""
        step("Check that application has been created and started")
        app_list = Application.get_list()
        self.__application = next((app for app in app_list if app.name.startswith(self.__service.name)), None)
        assert self.__application is not None, "Application for {} not found".format(self.__service.name)
        self.__application.ensure_started()

    def _validate_application_bound(self, expected_bindings):
        """Check if application has been properly bound."""
        step("Check that application has been properly bound")
        self.__validate_bound_services(expected_bindings)
        self.__validate_requested_bound(expected_bindings)

    def _validate_instance_has_been_removed(self):
        """Validate that service instance has been properly removed."""
        step("Check that service instance was deleted from services list")
        service_list = ServiceInstance.get_list()
        assert self.__service.name not in [i.name for i in service_list], "Service found on services list"

    def _validate_application_has_been_removed(self):
        """Validate that application has been properly removed."""
        if self.application:
            step("Check that application was deleted from application list")
            app_name = self.__service.name + "-{}".format(self.__service.guid[:8])
            app = next((a for a in Application.api_get_list(self.__service.space_guid) if a.name == app_name), None)
            assert app is None, "Application was found"

    def _validate_bindings_have_been_removed(self):
        """Validate that all bindings have been properly removed."""
        if self.application_bindings:
            step("Check that all bound service instances were deleted")
            service_instances = [s.name for s in ServiceInstance.api_get_list(self.__service.space_guid)]
            for service in self.application_bindings.keys():
                assert service not in service_instances

    def __validate_bound_services(self, expected_bindings):
        """Check if all bound services are in requested application bindings."""
        service_list = ServiceInstance.api_get_list(self.__service.space_guid)
        for binding in self.__application.get_bindings():
            instance = next((si for si in service_list if si.guid == binding.id), None)
            assert instance is not None, "Bound service instance not found"
            assert instance.service_label in expected_bindings, \
                "Invalid bound to {} instance".format(instance.service_label)
            self.__application_bindings[instance.service_label] = instance

    def __validate_requested_bound(self, expected_bindings):
        """Check if all requested services have been bound."""
        for binding in expected_bindings:
            assert binding in self.__application_bindings.keys(), \
                 "Application bound to {} instance not found".format(binding)

    @staticmethod
    def __validate_property(property_name, property_value):
        """Check if given property value is not empty."""
        if not property_value:
            raise ServiceInstanceValidatorEmptyPropertyException(property_name)


class ServiceInstanceValidatorEmptyPropertyException(Exception):
    TEMPLATE = "Service instance property with name {} is empty."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))
