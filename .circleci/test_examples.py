import pytest
from datetime import datetime

import os
from ecosystem_tests.dorkl import (
    basic_blueprint_test,
    update_plugin_on_manager)

plugin_path = os.path.join(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir)
    )
)
update_plugin_on_manager(
    plugin_path, 'cloudify-vcloud-plugin', ['cloudify_vcd', 'vcd_plugin_sdk'])

blueprint_list = ['examples/test.yaml']
TEST_ID = 'test-{0}'.format(datetime.now().strftime("%Y%m%d%H%M"))


@pytest.fixture(scope='function', params=blueprint_list)
def blueprint_examples(request, test_id=TEST_ID):
    basic_blueprint_test(
        request.param,
        test_id,
        inputs='',
        timeout=3000)


def test_blueprints(blueprint_examples):
    assert blueprint_examples is None
