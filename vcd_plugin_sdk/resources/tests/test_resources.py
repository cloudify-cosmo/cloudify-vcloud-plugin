import os
import mock
import pytest
from io import BytesIO

from pyvcloud.vcd.vdc import VDC as pyvcloud_vdc
from pyvcloud.vcd.vapp import VApp as pyvcloud_vapp
from pyvcloud.vcd.client import Client as pyvcloud_client
from pyvcloud.vcd.gateway import Gateway as pyvcloud_gateway
from pyvcloud.vcd.vdc_network import VdcNetwork as pyvcloud_network

from ..disk import (
    VCloudISO,
    VCloudDisk,
    VCloudMedia)
from ..network import (
    VCloudNetwork,
    VCloudGateway)
from ..base import VCloudResource

from ...connection import VCloudConnect
from ...exceptions import VCloudSDKException
from ...tests import (TEST_CONFIG, TEST_CREDENTIALS)


@mock.patch('pyvcloud.vcd.vdc.VDC.get_vapp')
@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_resource(*_, **__):
    logger = mock.Mock()
    tasks = mock.Mock()
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    resource = VCloudResource(vcloud_connect, 'vdc', 'vapp', tasks)
    assert isinstance(resource.client, pyvcloud_client)
    assert resource.tasks == tasks
    assert resource.connection == vcloud_connect
    assert isinstance(resource.vdc, pyvcloud_vdc)
    resource.task_successful(mock.Mock())
    assert resource.client.get_task_monitor.called
    assert isinstance(resource.vapp, pyvcloud_vapp)
    assert isinstance(resource.get_vapp('foo'), pyvcloud_vapp)
    assert resource.get_template('foo', 'bar') is not None


@mock.patch('pyvcloud.vcd.vdc.VDC.get_vapp')
@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_media(*_, **__):
    logger = mock.Mock()
    tasks = mock.Mock()
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    config = {'catalog_name': 'foo', 'file_name': 'bar'}
    vcloud_media = VCloudMedia('foo', vcloud_connect, 'vdc', config, tasks)
    media_obj = mock.Mock()
    vcloud_media._media = media_obj
    E = {'href': 'foo/bar'}
    vcloud_media._media.Entity = E
    assert vcloud_media.name == 'foo.iso'
    assert vcloud_media.catalog_name == 'foo'
    assert vcloud_media.id == 'bar'
    assert vcloud_media.exposed_data == {
        'name': vcloud_media.name,
        'catalog_name': vcloud_media.catalog_name,
        'id': vcloud_media.id,
        'href': vcloud_media.href
    }
    assert vcloud_media.href == 'foo/bar'
    assert vcloud_media._entity == E
    assert vcloud_media.media == media_obj
    vcloud_media.get_media('foo', 'bar')
    assert vcloud_media.connection.org.get_catalog_item.called
    vcloud_media.upload()
    assert vcloud_media.connection.org.upload_media.called
    vcloud_media.delete()
    assert vcloud_media.connection.org.delete_catalog_item.called


def test_vcloud_iso():
    config = {
        'vol_ident': 'cidata',
        'sys_ident': '',
        'files': {'ISO/FOLDER/content.json': 'test content'}
    }
    iso = VCloudISO(config)
    path = iso.file
    assert os.path.exists(path)
    assert iso.file == path
    assert isinstance(iso.iso_material, BytesIO)
    assert iso.iso_material_size == 71680
    iso.delete()
    assert not os.path.exists(path)


@mock.patch('pyvcloud.vcd.vdc.VDC.get_disk')
@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_disk(*_, **__):
    logger = mock.Mock()
    tasks = {'create': [[{'id': 'bar'}, {'href': 'foo/bar'}]], 'delete': []}
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    config = {'size': 2097152, 'description': 'test disk'}
    vcloud_disk = VCloudDisk('foo', vcloud_connect, 'vdc', config, tasks)
    assert vcloud_disk.name == 'foo'
    assert vcloud_disk.href == 'foo/bar'
    assert vcloud_disk._get_identifier('id') == 'bar'
    assert 'id', 'href' in vcloud_disk.exposed_data
    result = vcloud_disk.disk
    assert vcloud_disk.vdc.get_disk.called
    vcloud_disk.vdc.client.get_api_version = (lambda: '33')
    assert vcloud_disk.get_disk() == result
    vcloud_disk.create()
    vcloud_disk.delete()


@mock.patch('pyvcloud.vcd.vdc.VDC.get_routed_orgvdc_network')
@mock.patch('pyvcloud.vcd.vdc.VDC.get_direct_orgvdc_network')
@mock.patch('pyvcloud.vcd.vdc.VDC.get_isolated_orgvdc_network')
@mock.patch('pyvcloud.vcd.vdc.VDC.get_gateway', return_value={'href': 'foo'})
@mock.patch('pyvcloud.vcd.platform.Platform.get_external_network',
            return_value={'href': 'foo'})
@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_network(*_, **__):
    logger = mock.Mock()
    tasks = {'create': [[{'id': 'bar'}, {'href': 'foo/bar'}]], 'delete': []}
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    for network_type, config in [('routed_vdc_network',
                                  {'gateway_name': 'foo',
                                   'network_cidr': '1.1.1.1/1'}),
                                 ('isolated_vdc_network',
                                  {'network_cidr': '1.1.1.1/1'}),
                                 ('directly_connected_vdc_network',
                                  {'parent_network_name': 'foo'})]:
        vcloud_network = VCloudNetwork(
            'foo', network_type, vcloud_connect, 'vdc', 'vapp', config, tasks)
        assert vcloud_network.name == 'foo'
        assert isinstance(vcloud_network.network, pyvcloud_network)
        assert isinstance(vcloud_network.allocated_addresses, list)
        assert isinstance(vcloud_network.connected_vapps, list)
        assert 'allocated_ips', 'resource' in vcloud_network.exposed_data
        assert isinstance(vcloud_network.get_network('foo', network_type),
                          pyvcloud_network)
        with pytest.raises(VCloudSDKException):
            vcloud_network.get_network('foo')
            vcloud_network.get_network(network_type=network_type)
            vcloud_network.get_network('foo', 'bar')
        vcloud_network.create()
        if network_type == 'routed_vdc_network':
            assert vcloud_network.client.post_linked_resource.call_count == 1
        if network_type == 'isolated_vdc_network':
            assert vcloud_network.client.post_linked_resource.call_count == 2
        if network_type == 'directly_connected_vdc_network':
            assert vcloud_network.client.post_linked_resource.call_count == 3
        vcloud_network.delete()
        if network_type == 'routed_vdc_network':
            assert vcloud_network.client.delete_resource.call_count == 1
        if network_type == 'isolated_vdc_network':
            assert vcloud_network.client.delete_resource.call_count == 2
        if network_type == 'directly_connected_vdc_network':
            assert vcloud_network.client.delete_resource.call_count == 3
        vcloud_network.add_static_ip_pool_and_dns(
            ip_ranges_param=['1.1.1.1/1-2.2.2.2/2'])
        assert vcloud_network.client.put_linked_resource.called
        vcloud_network.remove_static_ip_pool(
            ip_range_param=['1.1.1.1/1-2.2.2.2/2'])
        assert vcloud_network.client.put_linked_resource.called


@mock.patch('pyvcloud.vcd.gateway.Gateway._build_dhcp_href')
@mock.patch('pyvcloud.vcd.gateway.Gateway.get_firewall_rules')
@mock.patch('pyvcloud.vcd.gateway.Gateway._build_nat_rule_href')
@mock.patch('pyvcloud.vcd.gateway.Gateway.list_firewall_objects')
@mock.patch('pyvcloud.vcd.gateway.Gateway._build_static_routes_href')
@mock.patch('pyvcloud.vcd.gateway.Gateway._build_firewall_rule_href')
@mock.patch('pyvcloud.vcd.vdc.VDC.get_gateway', return_value={'href': 'foo'})
@mock.patch('pyvcloud.vcd.platform.Platform.get_external_network',
            return_value={'href': 'foo'})
@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_gateway(*_, **__):
    logger = mock.Mock()
    tasks = {'create': [[{'id': 'bar'}, {'href': 'foo/bar'}]], 'delete': []}
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    config = {}
    vcloud_gateway = VCloudGateway('foo', vcloud_connect, 'vdc', config, tasks)
    assert vcloud_gateway.name == 'foo'
    assert isinstance(vcloud_gateway.gateway, pyvcloud_gateway)
    assert isinstance(vcloud_gateway.firewall_rules, list)
    assert isinstance(vcloud_gateway.firewall_objects, dict)
    assert 'source', 'destination' in vcloud_gateway.firewall_objects
    ___ = vcloud_gateway.default_gateway
    assert vcloud_gateway.client.get_resource.called
    assert isinstance(vcloud_gateway.static_routes, dict)
    assert isinstance(vcloud_gateway.nat_rules, list)
    assert isinstance(vcloud_gateway.dhcp_pools, list)
    assert isinstance(vcloud_gateway.exposed_data, dict)
    vcloud_gateway.get_gateway()
    assert vcloud_gateway.vdc.get_gateway.called


@mock.patch('pyvcloud.vcd.gateway.Gateway._build_dhcp_href')
@mock.patch('pyvcloud.vcd.gateway.Gateway.get_firewall_rules')
@mock.patch('pyvcloud.vcd.gateway.Gateway._build_nat_rule_href')
@mock.patch('pyvcloud.vcd.gateway.Gateway.list_firewall_objects')
@mock.patch('pyvcloud.vcd.gateway.Gateway._build_static_routes_href')
@mock.patch('pyvcloud.vcd.gateway.Gateway._build_firewall_rule_href')
@mock.patch('pyvcloud.vcd.firewall_rule.FirewallRule._build_network_href')
@mock.patch('pyvcloud.vcd.vdc.VDC.get_gateway',
            return_value={'href': 'foo'})
@mock.patch('pyvcloud.vcd.platform.Platform.get_external_network',
            return_value={'href': 'foo'})
@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_gateway_firewall_rule(*_, **__):

    logger = mock.Mock()
    tasks = {'create': [[{'id': 'bar'}, {'href': 'foo/bar'}]], 'delete': []}
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    config = {}
    vcloud_gateway = VCloudGateway('foo', vcloud_connect, 'vdc', config, tasks)

    try:
        vcloud_gateway.create_firewall_rule('foo')
    except VCloudSDKException:
        assert vcloud_gateway.client.put_resource.called
        assert vcloud_gateway.client.put_resource.call_count == 1

    firewall_rule = mock.Mock()

    def delete():
        return mock.Mock()
    firewall_rule.delete.side_effect = delete

    with mock.patch('vcd_plugin_sdk.resources.network.'
                    'VCloudGateway.infer_rule',
                    return_value=firewall_rule):
        vcloud_gateway.delete_firewall_rule('foo', 'bar')
        assert firewall_rule.delete.called

    assert isinstance(vcloud_gateway.get_list_of_rule_ids(), list)

    with mock.patch('vcd_plugin_sdk.resources.network.'
                    'FirewallRule') as firewall_rule:
        firewall_rule.resource = mock.Mock()
        firewall_rule_list = ['id']
        with mock.patch('vcd_plugin_sdk.resources.network.'
                        'VCloudGateway.get_list_of_rule_ids',
                        return_value=firewall_rule_list):
            try:
                vcloud_gateway.infer_rule(
                    firewall_rule().resource.name, ['id'], True)
            except VCloudSDKException:
                pytest.fail('Infer rule failed to return a rule.')

            try:
                vcloud_gateway.infer_rule(
                    firewall_rule().resource.name, ['no-id'])
            except VCloudSDKException:
                pytest.fail('Infer rule failed to return a rule.')


@mock.patch('pyvcloud.vcd.gateway.Gateway._build_nat_rule_href')
@mock.patch('pyvcloud.vcd.vdc.VDC.get_gateway',
            return_value={'href': 'foo'})
@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_gateway_nat_rule(*_, **__):
    logger = mock.Mock()
    tasks = {'create': [[{'id': 'bar'}, {'href': 'foo/bar'}]], 'delete': []}
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    config = {}
    vcloud_gateway = VCloudGateway('foo', vcloud_connect, 'vdc', config, tasks)
    rule_definition = {
        'action': 'dnat',
        'original_address': '10.10.4.2',
        'translated_address': '11.11.4.2',
        'description': 'Test blueprint example 1'}
    assert isinstance(vcloud_gateway.create_nat_rule(rule_definition), dict)

    with mock.patch('vcd_plugin_sdk.resources.network.NatRule'):
        assert isinstance(vcloud_gateway.delete_nat_rule('foo'),
                          mock.MagicMock)

    info = {
        'Action': 'dnat',
        'OriginalAddress': '10.10.4.2',
        'TranslatedAddress': '11.11.4.2',
        'Description': 'Test blueprint example 1'}

    assert isinstance(
        vcloud_gateway.get_nat_rule_from_definition(rule_definition), dict)
    assert vcloud_gateway.compare_nat_rule(info, rule_definition)


@mock.patch('pyvcloud.vcd.gateway.Gateway._build_dhcp_href')
@mock.patch('pyvcloud.vcd.vdc.VDC.get_gateway',
            return_value={'href': 'foo'})
@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_gateway_dhcp_pool(*_, **__):
    logger = mock.Mock()
    tasks = {'create': [[{'id': 'bar'}, {'href': 'foo/bar'}]], 'delete': []}
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    config = {}
    vcloud_gateway = VCloudGateway('foo', vcloud_connect, 'vdc', config, tasks)
    pool_definition = {'ip_range': '192.170.2.2-192.170.2.100'}
    with mock.patch('vcd_plugin_sdk.resources.network.'
                    'VCloudGateway.get_dhcp_pool_from_ip_range'):
        assert isinstance(vcloud_gateway.add_dhcp_pool(pool_definition),
                          mock.MagicMock)
    with mock.patch('vcd_plugin_sdk.resources.network.'
                    'VCloudGateway.get_dhcp_pool_from_ip_range'):
        assert isinstance(vcloud_gateway.delete_dhcp_pool(pool_definition),
                          mock.MagicMock)

    vcloud_gateway.get_dhcp_pool_from_ip_range(pool_definition['ip_range'])
    assert vcloud_gateway.client.get_resource.call_count == 4


@mock.patch('pyvcloud.vcd.gateway.Gateway._build_static_routes_href')
@mock.patch('pyvcloud.vcd.vdc.VDC.get_gateway',
            return_value={'href': 'foo'})
@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_gateway_static_route(*_, **__):
    logger = mock.Mock()
    tasks = {'create': [[{'id': 'bar'}, {'href': 'foo/bar'}]], 'delete': []}
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    config = {}
    vcloud_gateway = VCloudGateway('foo', vcloud_connect, 'vdc', config, tasks)
    assert isinstance(vcloud_gateway.get_static_routes(), list)
    vcloud_gateway.get_static_route_from_network('foo')

    mock_return = mock.Mock()
    mock_return.resource_id = 'foo'
    with mock.patch('vcd_plugin_sdk.resources.network.'
                    'VCloudGateway.get_static_routes',
                    return_value=[mock_return]):
        assert vcloud_gateway.get_static_route_from_network('foo') ==\
               mock_return
    route_definition = {
        'network': '192.170.3.0/24',
        'next_hop': '192.168.1.1',
        'description': 'Test blueprint example'
    }
    vcloud_gateway.add_static_route(route_definition)
    assert vcloud_gateway.client.put_resource.call_count == 1
    with mock.patch('vcd_plugin_sdk.resources.network.'
                    'VCloudGateway.get_static_route_from_network',
                    return_value=mock_return):
        vcloud_gateway.delete_static_route(route_definition)
        assert mock_return.delete_static_route.called