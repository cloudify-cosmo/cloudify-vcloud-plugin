import mock

from cloudify.manager import DirtyTrackingDict

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
