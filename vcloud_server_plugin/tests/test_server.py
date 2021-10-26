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

from .. server import create, delete, configure, start, stop
from cloudify_vcd.legacy.tests import create_ctx, DEFAULT_NODE_PROPS


def get_vm_ctx(existing=False,
               resource_id=None,
               server=None):
    """
    Generate the node props for use in the test.
    :param existing: whether to create or not
    :param resource_id: name of the resource
    :param server: the server resource config
    :param gateway: name of the edge gateway
    :return:
    """
    server = server or {
        'name': 'foo',
        'catalog': 'acme',
        'template': 'taco',
        'hardware': {
            'memory': 1024,
            'cpu': 1,
        },
        'guest_customization': {
            'computer_name': 'bar'
        }

    }
    server_node_props = {'server': server}
    server_node_props.update(
        deepcopy(DEFAULT_NODE_PROPS))
    server_node_props['use_external_resource'] = existing
    server_node_props['resource_id'] = resource_id
    return server_node_props


@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('vcd_plugin_sdk.resources.vapp.VCloudVM.exists', return_value=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_create_external_vm(*_, **__):
    server_node_props = get_vm_ctx(True, 'foo')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props)
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        create(ctx=_ctx)


@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.resources.vapp.VCloudVM.get_vm')
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('vcd_plugin_sdk.resources.vapp.VCloudVM.exists', return_value=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_delete_external_vm(*_, **__):
    server_node_props = get_vm_ctx(True, 'foo')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props)
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        delete(ctx=_ctx)


@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('vcd_plugin_sdk.resources.vapp.VCloudVM.exists', return_value=True)
def test_configure_external_vm(*_, **__):
    server_node_props = get_vm_ctx(True, 'foo')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props)
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        configure(ctx=_ctx)


@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('vcd_plugin_sdk.resources.vapp.VCloudVM.exists', return_value=True)
def test_start_external_vm(*_, **__):
    server_node_props = get_vm_ctx(True, 'foo')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props)
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        start(ctx=_ctx)


@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('vcd_plugin_sdk.resources.vapp.VCloudVM.exists', return_value=True)
def test_stop_external_vm(*_, **__):
    server_node_props = get_vm_ctx(True, 'foo')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props)
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        stop(ctx=_ctx)


@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_create_vm(*_, **__):
    server_node_props = get_vm_ctx(resource_id='foo')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props)
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        create(ctx=_ctx)


@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_configure_vm(*_, **__):
    server_node_props = get_vm_ctx(resource_id='foo')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props)
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        configure(ctx=_ctx)


@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_start_vm(*_, **__):
    server_node_props = get_vm_ctx(resource_id='foo')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props)
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        start(ctx=_ctx)


@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_stop_vm(*_, **__):
    server_node_props = get_vm_ctx(resource_id='foo')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props)
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        stop(ctx=_ctx)


@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.resources.vapp.VCloudVM.get_vm')
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('vcd_plugin_sdk.resources.vapp.VCloudVM.exists', return_value=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_delete_vm(*_, **__):
    server_node_props = get_vm_ctx(resource_id='foo')
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props)
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        delete(ctx=_ctx)
