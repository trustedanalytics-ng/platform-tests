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
from mock import Mock, patch

from cleanup_all_test_data import cleanup_test_data
from modules.tap_object_model import DataSet, Invitation, Transfer, User, Application, ServiceInstance, \
    ServiceOffering, ScoringEngineModel
from modules.test_names import generate_test_object_name

mock_data_set = Mock(title=generate_test_object_name())
mock_transfer = Mock(title=generate_test_object_name())
mock_user = Mock(username=generate_test_object_name())
mock_invitation = Mock(username=generate_test_object_name())
mock_application = Mock()
mock_application.name = generate_test_object_name()
mock_service = Mock()
mock_service.name = generate_test_object_name()
mock_offering = Mock(label=generate_test_object_name())
mock_model = Mock()
mock_model.name = generate_test_object_name()


@patch.object(DataSet, 'api_get_list', lambda: [mock_data_set])
@patch.object(Transfer, 'api_get_list', lambda: [mock_transfer])
@patch.object(User, 'get_list_in_organization', lambda **kwargs: [mock_user])
@patch.object(Invitation, 'api_get_list', lambda: [mock_invitation])
@patch.object(Application, 'get_list', lambda: [mock_application])
@patch.object(ServiceInstance, 'get_list', lambda: [mock_service])
@patch.object(ServiceOffering, 'get_list', lambda: [mock_offering])
@patch.object(ScoringEngineModel, 'get_list', lambda **kwargs: [mock_model])
def test_dataset_is_cleaned_up():
    cleanup_test_data()

    mock_data_set.cleanup.assert_any_call()
    mock_transfer.cleanup.assert_any_call()
    mock_user.cleanup.assert_any_call()
    mock_invitation.cleanup.assert_any_call()
    mock_application.cleanup.assert_any_call()
    mock_service.cleanup.assert_any_call()
    mock_offering.cleanup.assert_any_call()
    mock_model.cleanup.assert_any_call()
