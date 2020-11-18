import mock

from pyvcloud.vcd.org import Org as pyvcloud_org
from pyvcloud.vcd.client import Client as pyvcloud_client

from . import TEST_CONFIG, TEST_CREDENTIALS, TEST_CLIENT_CONFIG
from ..connection import (
    VCloudConnect,
    VCloudCredentials,
    VCloudClientConfiguration
)


@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_connect(_, __):
    logger = mock.Mock()
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    assert vcloud_connect.client_config.asdict() == TEST_CLIENT_CONFIG
    assert vcloud_connect.credentials.asdict() == TEST_CREDENTIALS
    assert vcloud_connect.logger == logger
    assert isinstance(vcloud_connect.client, pyvcloud_client)
    assert isinstance(vcloud_connect.org, pyvcloud_org)
    assert isinstance(vcloud_connect.get_org('foo'), pyvcloud_org)


def test_vcloud_client_configuration():
    logger = mock.Mock()
    vcloud_client_config = VCloudClientConfiguration(logger, **TEST_CONFIG)
    assert vcloud_client_config.asdict() == TEST_CLIENT_CONFIG


def test_vcloud_credentials():
    logger = mock.Mock()
    vcloud_credentials = VCloudCredentials(logger, **TEST_CREDENTIALS)
    assert vcloud_credentials.asdict() == TEST_CREDENTIALS
