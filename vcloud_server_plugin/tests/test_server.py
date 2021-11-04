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

from copy import deepcopy
from mock import patch, MagicMock
from cloudify.state import current_ctx

from .. server import create, delete, configure, start, stop
from vcloud_network_plugin.tests.test_port import get_port_ctx
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


@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('vcd_plugin_sdk.resources.vapp.VCloudVM.exists', return_value=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_create_external_vm(*_, **__):
    server_node_props = get_vm_ctx(True, 'foo')
    _ctx = create_ctx(
        node_id='server',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props,
    )
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        create(ctx=_ctx)
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'


@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
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
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'


@patch('pyvcloud.vcd.vapp.VApp.get_vm')
@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
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
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'


@patch('pyvcloud.vcd.vapp.VApp.get_vm')
@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
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
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'


@patch('pyvcloud.vcd.vapp.VApp.get_vm')
@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
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
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'


@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_create_vm(*_, **__):
    server_node_props = get_vm_ctx(resource_id='foo')
    _port1_ctx = create_ctx(
        node_id='port1',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=get_port_ctx(),
        runtime_props={
            'network_name': 'port1_network',
            'port': {
                'ip_address': '10.10.10.1'
            }
        }
    )
    _port2_ctx = create_ctx(
        node_id='port2',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=get_port_ctx('2', False),
        runtime_props={
            'network_name': 'port2_network',
            'port': {
                'ip_address': '10.10.10.2'
            }
        }
    )
    rels = [
        MagicMock(
            name='port1',
            target=_port1_ctx,
            type_hierarchy=[
                'cloudify.vcloud.server_connected_to_port',
                'cloudify.relationships.connected_to'
            ]
        ),
        MagicMock(
            name='port2',
            target=_port2_ctx,
            type_hierarchy=[
                'cloudify.vcloud.server_connected_to_port',
                'cloudify.relationships.connected_to'
            ]
        ),
    ]
    _ctx = create_ctx(
        node_id='server',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props,
        relationships=rels
    )
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        create(ctx=_ctx)
    assert '__VM_CREATE_VAPP' in _ctx.instance.runtime_properties
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert _ctx.instance.runtime_properties['server']['network'] == \
        'port1_network'
    assert _ctx.instance.runtime_properties['server']['ip_address'] == \
        '10.10.10.1'


@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_create_vm_no_primary_port(*_, **__):
    server_node_props = get_vm_ctx(resource_id='foo')
    _port1_ctx = create_ctx(
        node_id='port1',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=get_port_ctx(primary=False),
        runtime_props={
            'network_name': 'port1_network',
            'port': {
                'ip_address': '10.10.10.1'
            }
        }
    )
    _port2_ctx = create_ctx(
        node_id='port2',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=get_port_ctx('2', False),
        runtime_props={
            'network_name': 'port2_network',
            'port': {
                'ip_address': '10.10.10.2'
            }
        }
    )
    rels = [
        MagicMock(
            name='port1',
            target=_port1_ctx,
            type_hierarchy=[
                'cloudify.vcloud.server_connected_to_port',
                'cloudify.relationships.connected_to'
            ]
        ),
        MagicMock(
            name='port2',
            target=_port2_ctx,
            type_hierarchy=[
                'cloudify.vcloud.server_connected_to_port',
                'cloudify.relationships.connected_to'
            ]
        ),
    ]
    _ctx = create_ctx(
        node_id='server',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props,
        relationships=rels
    )
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        create(ctx=_ctx)
    assert '__VM_CREATE_VAPP' in _ctx.instance.runtime_properties
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert _ctx.instance.runtime_properties['server']['network'] == \
        'port2_network'


@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_create_vm_port_network(*_, **__):
    server_node_props = get_vm_ctx(resource_id='foo')
    _port1_props = get_port_ctx()
    _port1_props['port']['network'] = 'port1_port_network'
    _port1_ctx = create_ctx(
        node_id='port1',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=_port1_props,
        runtime_props={
            'network_name': 'port1_network',
            'port': {
                'ip_address': '10.10.10.5'
            }
        }
    )
    _port2_ctx = create_ctx(
        node_id='port2',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=get_port_ctx('2', False),
        runtime_props={
            'network_name': 'port2_network',
            'port': {
                'ip_address': '10.10.10.2'
            }
        }
    )
    rels = [
        MagicMock(
            name='port1',
            target=_port1_ctx,
            type_hierarchy=[
                'cloudify.vcloud.server_connected_to_port',
                'cloudify.relationships.connected_to'
            ]
        ),
        MagicMock(
            name='port2',
            target=_port2_ctx,
            type_hierarchy=[
                'cloudify.vcloud.server_connected_to_port',
                'cloudify.relationships.connected_to'
            ]
        ),
    ]
    _ctx = create_ctx(
        node_id='server',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props,
        relationships=rels
    )
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        create(ctx=_ctx)
    assert '__VM_CREATE_VAPP' in _ctx.instance.runtime_properties
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert _ctx.instance.runtime_properties['server']['network'] == \
        'port1_network'
    assert _ctx.instance.runtime_properties['server']['ip_address'] == \
        '10.10.10.5'


@patch('pyvcloud.vcd.vapp.VApp.get_vm')
@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
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
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'


@patch('pyvcloud.vcd.vapp.VApp')
@patch('cloudify_vcd.legacy.compute.tasks.VCloudVM')
@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('cloudify_vcd.legacy.compute.tasks.get_last_task')
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
@patch('cloudify_vcd.legacy.compute.tasks.check_if_task_successful',
       return_value=True)
def test_configure_vm_with_two_ports(*_, **__):
    server_node_props = get_vm_ctx(resource_id='foo')
    _port1_ctx = create_ctx(
        node_id='port1',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=get_port_ctx(),
        runtime_props={
            'network_name': 'port1_network',
            'port': {
                'network_name': 'port1_network',
                'ip_address': '10.10.10.1'
            }
        }
    )
    _port2_ctx = create_ctx(
        node_id='port2',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=get_port_ctx('2', False),
        runtime_props={
            'network_name': 'port2_network',
            'port': {
                'network_name': 'port2_network',
                'ip_address': '10.10.10.2'
            }
        }
    )
    rels = [
        MagicMock(
            name='port1',
            target=_port1_ctx,
            type_hierarchy=[
                'cloudify.vcloud.server_connected_to_port',
                'cloudify.relationships.connected_to'
            ]
        ),
        MagicMock(
            name='port2',
            target=_port2_ctx,
            type_hierarchy=[
                'cloudify.vcloud.server_connected_to_port',
                'cloudify.relationships.connected_to'
            ]
        ),
    ]
    _ctx = create_ctx(
        node_id='server',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props,
        relationships=rels,
        operation_name='cloudify.interfaces.lifecycle.configure'
    )
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        configure(ctx=_ctx)
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert _ctx.instance.runtime_properties['server']['network'] == \
        'port1_network'
    assert _ctx.instance.runtime_properties['server']['ip_address'] == \
        '10.10.10.1'


@patch('pyvcloud.vcd.vapp.VApp')
@patch('cloudify_vcd.legacy.compute.tasks.VCloudVM')
@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('cloudify_vcd.legacy.compute.tasks.get_last_task')
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
@patch('cloudify_vcd.legacy.compute.tasks.check_if_task_successful',
       return_value=True)
def test_configure_vm_with_two_ports_and_network_name(*_, **__):
    server_node_props = get_vm_ctx(resource_id='foo')
    _port1_props = get_port_ctx()
    _port1_props['port']['network'] = 'port1_port_network'
    _port1_ctx = create_ctx(
        node_id='port1',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=_port1_props,
        runtime_props={
            'network_name': 'port1_network',
            'port': {
                'network_name': 'port1_network',
                'ip_address': '10.10.10.5'
            }
        }
    )
    _port2_ctx = create_ctx(
        node_id='port2',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=get_port_ctx('2', False),
        runtime_props={
            'network_name': 'port2_network',
            'port': {
                'network_name': 'port1_network',
                'ip_address': '10.10.10.2'
            }
        }
    )
    rels = [
        MagicMock(
            name='port1',
            target=_port1_ctx,
            type_hierarchy=[
                'cloudify.vcloud.server_connected_to_port',
                'cloudify.relationships.connected_to'
            ]
        ),
        MagicMock(
            name='port2',
            target=_port2_ctx,
            type_hierarchy=[
                'cloudify.vcloud.server_connected_to_port',
                'cloudify.relationships.connected_to'
            ]
        ),
    ]
    _ctx = create_ctx(
        node_id='server',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props,
        relationships=rels
    )
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        configure(ctx=_ctx)
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert _ctx.instance.runtime_properties['server']['network'] == \
        'port1_network'
    assert _ctx.instance.runtime_properties['server']['ip_address'] == \
        '10.10.10.5'


@patch('pyvcloud.vcd.vapp.VApp.get_vm')
@patch('cloudify_vcd.legacy.compute.tasks.get_last_task')
@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
@patch('cloudify_vcd.legacy.decorators.get_last_task')
@patch('vcd_plugin_sdk.connection.Org', autospec=True)
@patch('pyvcloud.vcd.vapp.VApp.connect_org_vdc_network')
@patch('vcd_plugin_sdk.connection.Client', autospec=True)
@patch('cloudify_vcd.legacy.decorators.check_if_task_successful',
       return_value=True)
def test_configure_vm_port_no_primary_port(*_, **__):
    server_node_props = get_vm_ctx(resource_id='foo')
    _port1_ctx = create_ctx(
        node_id='port1',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=get_port_ctx(primary=False),
        runtime_props={
            'network_name': 'port1_network',
            'port': {
                'network_name': 'port1_network',
                'ip_address': '10.10.10.1'
            }
        }
    )
    _port2_ctx = create_ctx(
        node_id='port2',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=get_port_ctx('2', False),
        runtime_props={
            'network_name': 'port2_network',
            'port': {
                'ip_address': '10.10.10.2'
            }
        }
    )
    rels = [
        MagicMock(
            name='port1',
            target=_port1_ctx,
            type_hierarchy=[
                'cloudify.vcloud.server_connected_to_port',
                'cloudify.relationships.connected_to'
            ]
        ),
        MagicMock(
            name='port2',
            target=_port2_ctx,
            type_hierarchy=[
                'cloudify.vcloud.server_connected_to_port',
                'cloudify.relationships.connected_to'
            ]
        ),
    ]
    _ctx = create_ctx(
        node_id='server',
        node_type=[
            'cloudify.nodes.Compute',
            'cloudify.vcloud.nodes.Server'
        ],
        node_properties=server_node_props,
        relationships=rels
    )
    current_ctx.set(_ctx)
    with patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        configure(ctx=_ctx)
    assert '__VM_CREATE_VAPP' in _ctx.instance.runtime_properties
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert _ctx.instance.runtime_properties['server']['network'] == \
        'port2_network'
    assert _ctx.instance.runtime_properties['server']['ip_address'] == \
        '10.10.10.2'


@patch('pyvcloud.vcd.vapp.VApp.get_vm')
@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
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
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'


@patch('pyvcloud.vcd.vapp.VApp.get_vm')
@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
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
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'


@patch('cloudify_vcd.legacy.utils.NamedTemporaryFile')
@patch('cloudify_vcd.legacy.utils.get_deployment_dir')
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
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
