# Copyright (c) 2020 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mock import patch
from copy import deepcopy
from cloudify.state import current_ctx

from .. network import create, delete
from cloudify_vcd.legacy.tests import create_ctx, DEFAULT_NODE_PROPS


def get_network_ctx(existing=False,
                    resource_id=None,
                    network=None,
                    gateway=None):
    """
    Generate the node props for use in the test.
    :param existing: whether to create or not
    :param resource_id: name of the resource
    :param network: the network resource config
    :param gateway: name of the edge gateway
    :return:
    """

    network = network or {
        'static_range': '10.10.0.2-10.10.0.128',
        'gateway_ip': '10.10.0.1'
    }

    network_node_props = {'network': network}
    network_node_props.update(
        deepcopy(DEFAULT_NODE_PROPS))
    network_node_props['use_external_resource'] = existing
    network_node_props['resource_id'] = resource_id
    if gateway:
        network_node_props['vcloud_config']['edge_gateway'] = gateway
    return network_node_props


@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('pyvcloud.vcd.vdc.VDC.get_routed_orgvdc_network')
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('pyvcloud.vcd.vdc.VDC.get_gateway', return_value={'href': 'foo'})
def test_create_external_network_with_gateway(*_, **__):
    network_node_props = get_network_ctx(True, 'foo', gateway='baz')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Network',
            'cloudify.vcloud.nodes.Network'
        ],
        node_properties=network_node_props)
    current_ctx.set(_ctx)
    create(ctx=_ctx)


@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('pyvcloud.vcd.vdc.VDC.get_routed_orgvdc_network')
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('pyvcloud.vcd.vdc.VDC.get_gateway', return_value={'href': 'foo'})
def test_delete_external_network_with_gateway(*_, **__):
    network_node_props = get_network_ctx(True, 'foo', gateway='baz')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Network',
            'cloudify.vcloud.nodes.Network'
        ],
        node_properties=network_node_props)
    current_ctx.set(_ctx)
    delete(ctx=_ctx)


@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('pyvcloud.vcd.vdc.VDC.get_gateway', return_value={'href': 'foo'})
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
@patch('vcd_plugin_sdk.resources.network.VCloudNetwork.get_network',
       return_value=False)
def test_create_network_with_gateway(*_, **__):
    network_node_props = get_network_ctx(resource_id='foo', gateway='baz')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Network',
            'cloudify.vcloud.nodes.Network'
        ],
        node_properties=network_node_props)
    current_ctx.set(_ctx)
    create(ctx=_ctx)


@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('pyvcloud.vcd.vdc.VDC.get_routed_orgvdc_network')
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('pyvcloud.vcd.vdc.VDC.get_gateway', return_value={'href': 'foo'})
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_delete_network_with_gateway(*_, **__):
    network_node_props = get_network_ctx(resource_id='foo', gateway='baz')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Network',
            'cloudify.vcloud.nodes.Network'
        ],
        node_properties=network_node_props,
        operation_name='cloudify.interfaces.lifecycle.delete')
    current_ctx.set(_ctx)
    delete(ctx=_ctx)
