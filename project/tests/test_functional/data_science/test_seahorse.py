import pytest

from configuration import config
from modules.runner.tap_test_case import TapTestCase
from modules.service_tools.seahorse import Seahorse

class TestSeahorse(TapTestCase):
    seahorse_label = "k-seahorse-dev"
    tap_domain = config.CONFIG["domain"]
    username = config.CONFIG["admin_username"]
    password = config.CONFIG["admin_password"]

    def test_0_there_are_example_workflows(self):
        workflows = self.seahorse.get_workflows()
        assert len(workflows) > 5

    def test_1_workflow_can_be_cloned(self):
        some_workflow_id = self.seahorse.get_workflow_id_by_name('Text Message Spam Detection')
        self.seahorse.clone_workflow(some_workflow_id)

    def test_2_workflow_can_be_launched(self):
        workflow_id_to_be_cloned = self.seahorse.get_workflow_id_by_name('Text Message Spam Detection')
        cloned_workflow_id = self.seahorse.clone_workflow(workflow_id_to_be_cloned)
        self.seahorse.start_editing(cloned_workflow_id)
        self.seahorse.launch(cloned_workflow_id)
        self.seahorse.assert_n_nodes_completed_successfully(14)
        self.seahorse.stop_editing(cloned_workflow_id)

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def seahorse(cls):
        cls.seahorse = Seahorse('e06d477a-c8bb-48f0-baeb-3d709578d8af', 'b641e43e-b89b-4f32-b360-f1cf6bd1aa74')