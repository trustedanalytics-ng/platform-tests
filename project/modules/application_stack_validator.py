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

from .runner.tap_test_case import TapTestCase
from .tap_object_model import Application, ServiceBinding, ServiceInstance


class ApplicationStackValidator(object):
    def __init__(self, api_test: TapTestCase, service: ServiceInstance):
        self.__validate_property("name", service.name)
        self.__validate_property("guid", service.guid)
        self.__validate_property("space_guid", service.space_guid)
        self.__service = service
        self.__api_test = api_test
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
        self.__api_test.step("Check that service instance has been created")
        self.__api_test.assertInWithRetry(self.__service, ServiceInstance.api_get_list, self.__service.space_guid)

    def _validate_application_created(self):
        """Check if application for service instance has been properly created and started."""
        self.__api_test.step("Check that application has been created and started")
        app_list = Application.api_get_list(self.__service.space_guid)
        self.__application = next((app for app in app_list if app.name.startswith(self.__service.name)), None)
        self.__api_test.assertIsNotNone(self.__application, "Application for {} not found".format(self.__service.name))
        self.__application.ensure_started()

    def _validate_application_bound(self, expected_bindings):
        """Check if application has been properly bound."""
        self.__api_test.step("Check that application has been properly bound")
        self.__validate_bound_services(expected_bindings)
        self.__validate_requested_bound(expected_bindings)

    def _validate_instance_has_been_removed(self):
        """Validate that service instance has been properly removed."""
        self.__api_test.step("Check that service instance was deleted from services list")
        service_list = ServiceInstance.api_get_list(self.__service.space_guid)
        self.__api_test.assertNotIn(
            self.__service.name, [i.name for i in service_list], "Service found on services list")

    def _validate_application_has_been_removed(self):
        """Validate that application has been properly removed."""
        if self.application:
            self.__api_test.step("Check that application was deleted from application list")
            app_name = self.__service.name + "-{}".format(self.__service.guid[:8])
            app = next((a for a in Application.api_get_list(self.__service.space_guid) if a.name == app_name), None)
            self.__api_test.assertIsNone(app, "Application was found")

    def _validate_bindings_have_been_removed(self):
        """Validate that all bindings have been properly removed."""
        if self.application_bindings:
            self.__api_test.step("Check that all bound service instances were deleted")
            service_instances = [s.name for s in ServiceInstance.api_get_list(self.__service.space_guid)]
            for service in self.application_bindings.keys():
                self.__api_test.assertNotIn(service, service_instances)

    def __validate_bound_services(self, expected_bindings):
        """Check if all bound services are in requested application bindings."""
        service_list = ServiceInstance.api_get_list(self.__service.space_guid)
        bound_services = ServiceBinding.api_get_list(self.__application.guid)
        for bound_service in bound_services:
            instance = next((si for si in service_list if si.guid == bound_service.service_instance_guid), None)
            self.__api_test.assertIsNotNone(instance, "Bound service instance not found")
            self.__api_test.assertIn(instance.service_label, expected_bindings,
                                     "Invalid bound to {} instance".format(instance.service_label))
            self.__application_bindings[instance.service_label] = instance

    def __validate_requested_bound(self, expected_bindings):
        """Check if all requested services have been bound."""
        for binding in expected_bindings:
            self.__api_test.assertIn(binding, self.__application_bindings.keys(),
                                     "Application bound to {} instance not found".format(binding))

    @staticmethod
    def __validate_property(property_name, property_value):
        """Check if given property value is not empty."""
        if not property_value:
            raise ServiceInstanceValidatorEmptyPropertyException(property_name)


class ServiceInstanceValidatorEmptyPropertyException(Exception):
    TEMPLATE = "Service instance property with name {} is empty."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))
