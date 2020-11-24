import mock
import pytest

from cloudify.manager import DirtyTrackingDict
from cloudify.exceptions import (
    OperationRetry,
    NonRecoverableError)

from pyvcloud.vcd.exceptions import (
    BadRequestException,
    EntityNotFoundException)

from .test_utils import (
    get_mock_relationship_context,
    get_mock_node_instance_context)

from ..gateway_tasks import (
    configure_gateway,
    delete_gateway,
    create_firewall_rules,
    delete_firewall_rules,
    create_static_routes,
    delete_static_routes,
    create_dhcp_pools,
    delete_dhcp_pools,
    create_nat_rules,
    delete_nat_rules)

from ..disk_tasks import (
    create_disk,
    delete_disk,
    attach_disk,
    detach_disk)

from ..media_tasks import (
    create_media,
    delete_media,
    attach_media,
    detach_media
)

from ..network_tasks import (
    create_network,
    delete_network
)

from ..vapp_tasks import (
    create_vapp,
    stop_vapp,
    delete_vapp,
    create_vm,
    configure_vm,
    start_vm,
    stop_vm,
    delete_vm
)


@mock.patch('cloudify_vcd.constants.VCloudGateway.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_configure_gateway(*_, **__):
    operation = {'name': 'create', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'foo': 'bar'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.Gateway']
    configure_gateway(ctx=_ctx)
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert '__created' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.constants.VCloudGateway.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_delete_gateway(*_, **__):
    operation = {'name': 'delete', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'foo': 'bar'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.Gateway']
    delete_gateway(ctx=_ctx)
    assert '__deleted' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.constants.VCloudGateway.exposed_data')
@mock.patch('cloudify_vcd.constants.VCloudGateway.get_gateway')
@mock.patch('cloudify_vcd.constants.VCloudGateway.infer_rule')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_create_firewall_rules(*_, **__):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.Gateway'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'foo'})
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.FirewallRules'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            },
            'resource_config': {
                'foo': {
                    'source_values': ['taco'],
                    'destination_values': ['bell'],
                    'services': ['drive', 'thru']
                }
            }
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'bar'})
    )
    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    _ctx = get_mock_relationship_context(source=source, target=target)
    create_firewall_rules(ctx=_ctx)
    assert 'rules' in _ctx.target.instance.runtime_properties


@mock.patch('cloudify_vcd.constants.VCloudGateway.exposed_data')
@mock.patch('cloudify_vcd.constants.VCloudGateway.get_gateway')
@mock.patch('cloudify_vcd.constants.VCloudGateway.infer_rule')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_delete_firewall_rules(*_, **__):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.Gateway'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'foo'})
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.FirewallRules'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            },
            'resource_config': {
                'foo': {
                    'source_values': ['taco'],
                    'destination_values': ['bell'],
                    'services': ['drive', 'thru']
                }
            }
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict(
            {
                'resource_id': 'bar',
                'rules': {}
            }
        )
    )
    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    _ctx = get_mock_relationship_context(
        source=source, target=target)
    delete_firewall_rules(ctx=_ctx)


@mock.patch('cloudify_vcd.constants.VCloudGateway.exposed_data')
@mock.patch('cloudify_vcd.constants.VCloudGateway.get_gateway')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_create_static_routes(*_, **__):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.Gateway'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'foo'})
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.StaticRoutes'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            },
            'resource_config': [{'foo': 'bar'}]
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'bar'})
    )
    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    _ctx = get_mock_relationship_context(source=source, target=target)
    resource = create_static_routes(ctx=_ctx)
    assert resource.gateway.add_static_route.called


@mock.patch('cloudify_vcd.constants.VCloudGateway.exposed_data')
@mock.patch('cloudify_vcd.constants.VCloudGateway.get_gateway')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_delete_static_routes(*_, **__):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.Gateway'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'foo'})
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.StaticRoutes'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            },
            'resource_config': [{'foo': 'bar'}]
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'bar'})
    )
    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    _ctx = get_mock_relationship_context(
        source=source, target=target)
    # TODO: Need to figure out how to assert this one.
    delete_static_routes(ctx=_ctx)


@mock.patch('cloudify_vcd.constants.VCloudGateway.exposed_data')
@mock.patch('cloudify_vcd.constants.VCloudGateway.get_gateway')
@mock.patch('cloudify_vcd.constants.VCloudGateway.get_dhcp_pool_from_ip_range')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_create_dhcp_pools(*_, **__):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.Gateway'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'foo'})
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.DHCPPools'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            },
            'resource_config': [{'foo': 'bar'}]
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'bar'})
    )
    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    _ctx = get_mock_relationship_context(source=source, target=target)
    resource = create_dhcp_pools(ctx=_ctx)
    assert resource.gateway.add_dhcp_pool.called


@mock.patch('cloudify_vcd.constants.VCloudGateway.exposed_data')
@mock.patch('cloudify_vcd.constants.VCloudGateway.get_gateway')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_delete_dhcp_pools(*_, **__):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.Gateway'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'foo'})
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.DHCPPools'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            },
            'resource_config': [{'foo': 'bar'}]
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'bar'})
    )
    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    _ctx = get_mock_relationship_context(
        source=source, target=target)
    # TODO: Need to figure out how to assert this one.
    delete_dhcp_pools(ctx=_ctx)


@mock.patch('cloudify_vcd.constants.VCloudGateway.exposed_data')
@mock.patch('cloudify_vcd.constants.VCloudGateway.get_gateway')
@mock.patch('cloudify_vcd.constants.VCloudGateway.get_dhcp_pool_from_ip_range')
@mock.patch('cloudify_vcd.constants.VCloudGateway.create_nat_rule',
            return_value={'ID': 'foo'})
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_create_nat_rules(*_, **__):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.Gateway'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'foo'})
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.NatRules'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            },
            'resource_config': [{'foo': 'bar'}]
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'bar'})
    )
    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    _ctx = get_mock_relationship_context(source=source, target=target)
    create_nat_rules(ctx=_ctx)


@mock.patch('cloudify_vcd.constants.VCloudGateway.exposed_data')
@mock.patch('cloudify_vcd.constants.VCloudGateway.get_gateway')
@mock.patch('vcd_plugin_sdk.resources.network.NatRule')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_delete_nat_rules(*_, **__):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.Gateway'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'foo'})
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.NatRules'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            },
            'resource_config': [{'foo': 'bar'}]
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'bar'})
    )
    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    _ctx = get_mock_relationship_context(
        source=source, target=target)
    _ctx.target.instance.runtime_properties['rules'] = {'foo': 'bar'}
    # TODO: Need to figure out how to assert this one.
    delete_nat_rules(ctx=_ctx)


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudDisk.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_create_disk(*_, **__):
    operation = {'name': 'create', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'size': 1, 'description': 'foo'},
            'client_config': {'size': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.Disk']
    with mock.patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        create_disk(ctx=_ctx)
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert '__created' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudDisk.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_delete_disk(*_, **__):
    operation = {'name': 'delete', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'size': 1, 'description': 'foo'},
            'client_config': {'size': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.Disk']
    delete_disk(ctx=_ctx)
    assert '__deleted' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudVM.get_vapp')
@mock.patch('cloudify_vcd.constants.VCloudDisk.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_attach_disk(*_, **__):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.VM'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({
            'resource_id': 'foo',
            'data': {'vapp':' foo'}
        })
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.Disk'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            },
            'resource_config': {'size': 1, 'description': 'foo'},
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'bar'})
    )
    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    _ctx = get_mock_relationship_context(source=source, target=target)
    attach_disk(ctx=_ctx)
    assert _ctx.target.instance.runtime_properties['resource_id'] == 'bar'
    assert 'tasks' in _ctx.target.instance.runtime_properties


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudVM.get_vapp')
@mock.patch('cloudify_vcd.constants.VCloudDisk.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_detach_disk(*_, **__):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.VM'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({
            'resource_id': 'foo',
            'data': {'vapp':' foo'}
        })
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.Disk'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            },
            'resource_config': {'size': 1, 'description': 'foo'},
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'bar'})
    )
    operation = {'name': 'unlink', 'retry_number': 0}

    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    _ctx = get_mock_relationship_context(
        source=source, target=target, operation=operation)
    detach_disk(ctx=_ctx)
    # TODO: Figure what we can assert here.


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudMedia.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_create_media(*_, **__):
    operation = {'name': 'create', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'catalog_name': 'foo'},
            'iso': {'vol_ident': 'foo', 'sys_ident': '',
                    'files': {'ISO/FOLDER/content.json': 'baz'}},
            'client_config': {'size': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.Media']
    create_media(ctx=_ctx)
    # VCloud requires .iso suffix.
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo.iso'
    assert '__created' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudMedia.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_delete_media(*_, **__):
    operation = {'name': 'delete', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'catalog_name': 'foo'},
            'iso': {'vol_ident': 'foo', 'sys_ident': '',
                    'files': {'ISO/FOLDER/content.json': 'baz'}},
            'client_config': {'size': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.Media']
    delete_media(ctx=_ctx)
    assert '__deleted' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('pyvcloud.vcd.vm.VM.insert_cd_from_catalog')
@mock.patch('cloudify_vcd.constants.VCloudVM.get_vapp')
@mock.patch('cloudify_vcd.constants.VCloudMedia.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_attach_media(*_, **__):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.VM'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({
            'resource_id': 'foo',
            'data': {'vapp':' foo'}
        })
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.Media'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            },
            'resource_config': {'size': 1, 'description': 'foo'},
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'bar'})
    )
    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    _ctx = get_mock_relationship_context(source=source, target=target)
    attach_media(ctx=_ctx)
    assert _ctx.target.instance.runtime_properties['resource_id'] == 'bar.iso'
    assert 'tasks' in _ctx.target.instance.runtime_properties


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudVM.get_vapp')
@mock.patch('cloudify_vcd.constants.VCloudMedia.exposed_data')
@mock.patch('cloudify_vcd.constants.VCloudMedia.href', new='foo/bar')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_detach_media(*_, **__):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.VM'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({
            'resource_id': 'foo',
            'data': {'vapp':' foo'}
        })
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.Media'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            },
            'resource_config': {'size': 1, 'description': 'foo'},
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'bar'})
    )
    operation = {'name': 'unlink', 'retry_number': 0}

    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    _ctx = get_mock_relationship_context(
        source=source, target=target, operation=operation)
    detach_media(ctx=_ctx)
    # TODO: Figure what we can assert here.


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudNetwork.exposed_data')
@mock.patch('pyvcloud.vcd.vdc.VDC.get_gateway', return_value={'href': 'foo'})
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
@mock.patch('cloudify_vcd.network_tasks.find_resource_id_from_relationship_'
            'by_type', return_value='foo')
def test_create_network(*_, **__):
    operation = {'name': 'create', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'gateway_name': 'bar', 'network_cidr': '1.1.1.1/1'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.RoutedVDCNetwork']
    create_network(ctx=_ctx)
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert '__created' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.constants.VCloudNetwork.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_delete_network(*_, **__):
    operation = {'name': 'delete', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'foo': 'bar'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.RoutedVDCNetwork']
    delete_network(ctx=_ctx)
    assert '__deleted' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudvApp.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
@mock.patch('cloudify_vcd.vapp_tasks.find_resource_id_from_relationship_'
            'by_type', return_value='foo')
def test_create_vapp(*_, **__):
    operation = {'name': 'create', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'description': 'bar', 'fence_mode': 'baz'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.VApp']
    create_vapp(ctx=_ctx)
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert '__created' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.constants.VCloudvApp.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('pyvcloud.vcd.vdc.VDC.get_vapp', return_value={'href': 'foo'})
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_stop_vapp(*_, **__):
    operation = {'name': 'stop', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'description': 'bar', 'fence_mode': 'baz'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.VApp']
    stop_vapp(ctx=_ctx)
    # TODO: Figure out appropriate assert here.


@mock.patch('cloudify_vcd.constants.VCloudvApp.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('pyvcloud.vcd.vdc.VDC.get_vapp_href', return_value={'href': 'foo'})
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_delete_vapp(*_, **__):
    operation = {'name': 'delete', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'description': 'bar', 'fence_mode': 'baz'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.VApp']
    delete_vapp(ctx=_ctx)
    assert '__deleted' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
@mock.patch('cloudify_vcd.vapp_tasks.find_resource_id_from_relationship_'
            'by_type', return_value='foo')
def test_create_vm(*_, **__):
    operation = {'name': 'create', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'catalog': 'bar', 'template': 'baz'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.VM']
    with mock.patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        create_vm(ctx=_ctx)
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert '__created' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
@mock.patch('cloudify_vcd.vapp_tasks.find_resource_id_from_relationship_'
            'by_type', return_value='foo')
def test_create_vm_external(*_, **__):
    operation = {'name': 'create', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'resource_config': {'catalog': 'bar', 'template': 'baz'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.VM']
    with mock.patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        create_vm(ctx=_ctx)
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert '__created' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
@mock.patch('cloudify_vcd.vapp_tasks.find_resource_id_from_relationship_'
            'by_type', return_value='foo')
def test_create_vm_handles_bad_request(*_, **__):
    operation = {'name': 'create', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'catalog': 'bar', 'template': 'baz'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.VM']
    with mock.patch('cloudify_vcd.constants.VCloudVM.instantiate_vapp',
                    side_effect=BadRequestException(
                        400,
                        'foo',
                        {
                            'message': 'DUPLICATE_NAME',
                            'minorCode': 400
                        })):
        create_vm(ctx=_ctx)
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'
    assert '__created' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
@mock.patch('cloudify_vcd.vapp_tasks.find_resource_id_from_relationship_'
            'by_type', return_value='foo')
def test_create_vm_raises_bad_request(*_, **__):
    operation = {'name': 'create', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'catalog': 'bar', 'template': 'baz'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.VM']
    with mock.patch('cloudify_vcd.constants.VCloudVM.instantiate_vapp',
                    side_effect=EntityNotFoundException()):
        with pytest.raises(NonRecoverableError):
            create_vm(ctx=_ctx)


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
@mock.patch('cloudify_vcd.vapp_tasks.find_resource_id_from_relationship_'
            'by_type', return_value='foo')
def test_create_vm_raises_bad_request(*_, **__):
    operation = {'name': 'create', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'catalog': 'bar', 'template': 'baz'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.VM']
    with mock.patch('cloudify_vcd.constants.VCloudVM.instantiate_vapp',
                    side_effect=BadRequestException(
                        400,
                        'foo',
                        {
                            'message': 'is busy, '
                                       'cannot proceed with the operation',
                            'minorCode': 400
                        })):
        with pytest.raises(OperationRetry):
            create_vm(ctx=_ctx)


@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
@mock.patch('cloudify_vcd.vapp_tasks.find_resource_id_from_relationship_'
            'by_type', return_value='foo')
def test_configure_vm(*_, **__):
    operation = {'name': 'configure', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'catalog': 'bar', 'template': 'baz'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.VM']
    with mock.patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        configure_vm(ctx=_ctx)
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'


@mock.patch('pyvcloud.vcd.vapp.VApp.get_vm')
@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
@mock.patch('cloudify_vcd.vapp_tasks.find_resource_id_from_relationship_'
            'by_type', return_value='foo')
def test_start_vm(*_, **__):
    operation = {'name': 'start', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'catalog': 'bar', 'template': 'baz'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.VM']
    with mock.patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        start_vm(ctx=_ctx)
    assert _ctx.instance.runtime_properties['resource_id'] == 'foo'


@mock.patch('pyvcloud.vcd.vapp.VApp.get_vm')
@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
@mock.patch('cloudify_vcd.vapp_tasks.find_resource_id_from_relationship_'
            'by_type', return_value='foo')
def test_stop_vm(*_, **__):
    operation = {'name': 'stop', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'catalog': 'bar', 'template': 'baz'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.VM']
    with mock.patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        stop_vm(ctx=_ctx)
    # TODO: Figure out what to assert here. :(


@mock.patch('pyvcloud.vcd.vapp.VApp.get_vm')
@mock.patch('cloudify_vcd.decorators.get_last_task')
@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
@mock.patch('cloudify_vcd.vapp_tasks.find_resource_id_from_relationship_'
            'by_type', return_value='foo')
def test_delete_vm(*_, **__):
    operation = {'name': 'delete', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'catalog': 'bar', 'template': 'baz'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.vcloud.VM']
    with mock.patch('vcd_plugin_sdk.resources.base.VDC') as vdc:
        vdc.client.get_api_version = (lambda: '33')
        delete_vm(ctx=_ctx)
    assert '__deleted' in _ctx.instance.runtime_properties
