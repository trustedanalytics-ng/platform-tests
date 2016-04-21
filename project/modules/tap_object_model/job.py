#
# Copyright (c) 2015-2016 Intel Corporation
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

import datetime
import functools
import time
from enum import Enum

from ..exceptions import JobException
from ..http_calls import platform as api
from ..test_names import get_test_name


class TimeUnit(Enum):
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"


class ImportMode(Enum):
    INCREMENTAL = "Incremental"
    APPEND = "Append"
    OVERWRITE = "Overwrite"


class JobStatus(Enum):
    KILLED = "KILLED"
    SUCCEEDED = "SUCCEEDED"
    PREPARATION = "PREP"
    RUNNING = "RUNNING"


@functools.total_ordering
class Job(object):

    TIME_TEMPLATE = "%m/%d/%Y %H:%M %p"

    def __init__(self, app_name=None, app_path=None, actions=None, conf=None, coordinator_id=None, created_time=None,
                 end_time=None, id=None, last_mod_time=None, start_time=None, status=None, target_dirs=None, user=None,
                 frequency=None, time_unit=None, time_zone=None):
        self.app_name = app_name
        self.app_path = app_path
        self.actions = actions
        self.conf = conf
        self.coordinator_id = coordinator_id
        self.created_time = created_time
        self.end_time = end_time
        self.id = id
        self.last_mod_time = last_mod_time
        self.start_time = start_time
        self.status = status
        self.target_dirs = target_dirs
        self.user = user
        self.frequency = frequency
        self.time_unit = time_unit
        self.time_zone = time_zone

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.coordinator_id)

    def __eq__(self, other):
        return self.coordinator_id == other.coordinator_id

    def __lt__(self, other):
        return self.coordinator_id < other.coordinator_id

    @staticmethod
    def __validate_job_import_method(import_mode, last_value, check_column):
        if import_mode == ImportMode.INCREMENTAL and (last_value == "" or check_column == "" or last_value is None or
                                                      check_column is None):
            raise JobException("Incremental mode has to be accompanied by last_value and check_column")

    @staticmethod
    def __create_db_uri(db_hostname, port, db_name):
        return "jdbc:postgresql://{}:{}/{}".format(db_hostname, port, db_name)

    @classmethod
    def _from_api_response(cls, api_response):
        return cls(
            app_name=api_response["appName"],
            app_path=api_response["appPath"],
            actions=api_response["actions"],
            conf=api_response["conf"],
            coordinator_id=api_response["coordinatorId"],
            end_time=api_response["endTime"],
            id=api_response["id"],
            start_time=api_response["startTime"],
            status=api_response["status"],
            target_dirs=api_response["targetDirs"],
            user=api_response["user"]
        )

    @classmethod
    def api_get_list(cls, org_guid, amount=1, unit=TimeUnit.DAYS):
        response = api.api_get_jobs_list(org_guid, amount, unit)
        return [cls._from_api_response(job_data) for job_data in response]

    @classmethod
    def api_create(cls, org_guid, *, name=None, frequency_amount=None, frequency_unit=None, zone_id=None,
                   check_column=None, import_mode=None, db_hostname=None, db_name=None, port=None, last_value=None,
                   password=None, table=None, target_dir=None, username=None, end_job_minutes_later=None):
        name = get_test_name() if name is None else name
        start_job = datetime.datetime.now()
        end_job = start_job + datetime.timedelta(minutes=end_job_minutes_later)
        start = start_job.strftime(cls.TIME_TEMPLATE)
        end = end_job.strftime(cls.TIME_TEMPLATE)
        cls.__validate_job_import_method(import_mode, last_value, check_column)
        jdbc_uri = cls.__create_db_uri(db_hostname=db_hostname, port=port, db_name=db_name)
        coordinator_id = api.api_create_job(org_guid, name, start=start, end=end, amount=frequency_amount,
                                            unit=frequency_unit, zone_id=zone_id, check_column=check_column,
                                            import_mode=import_mode, jdbc_uri=jdbc_uri, last_value=last_value,
                                            password=password, table=table, target_dir=target_dir, username=username)
        return cls(app_name=name, coordinator_id=coordinator_id["id"])

    def api_update_job_details(self, org_guid):
        job_list = self.api_get_list(org_guid)
        for job in job_list:
            if self.id is not None:
                break
            if self.coordinator_id == job.coordinator_id:
                self.id = job.id
        response = api.api_get_job_details(org_guid, self.id)
        job = self._from_api_response(response)
        self.app_name = job.app_name
        self.actions = job.actions
        self.app_path = job.app_path
        self.conf = job.conf
        self.created_time = job.created_time
        self.start_time = job.start_time
        self.created_time = job.created_time
        self.end_time = job.end_time
        self.last_mod_time = job.last_mod_time
        self.status = job.status
        self.target_dirs = job.target_dirs
        self.user = job.user

    def ensure_successful(self, org_guid, timeout=60):
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(2)
            self.api_update_job_details(org_guid)
            if self.status == JobStatus.KILLED:
                raise AssertionError("Job failed to work and was killed")
            if self.status == JobStatus.SUCCEEDED:
                return


