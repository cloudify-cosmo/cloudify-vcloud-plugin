from copy import deepcopy

from mock import MagicMock
from cloudify.state import current_ctx

from .. port import creation_validation
from .test_network import get_network_ctx
from cloudify_vcd.legacy.tests import create_ctx, DEFAULT_NODE_PROPS


def get_port_ctx(num=None, primary=True):
    num = num or '1'
    port = {
        'ip_allocation_mode': 'manual',
        'ip_address': '10.10.10.{}'.format(num),
        'primary_interface': primary,
    }
    port_props = {'port': port}
    port_props.update(
        deepcopy(DEFAULT_NODE_PROPS))
    return port_props


def test_create_external_network_with_gateway(*_, **__):
    port_props = get_port_ctx()
    net_props = get_network_ctx(resource_id='foo-bar')
    _net_ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Network',
            'cloudify.vcloud.nodes.Network'
        ],
        node_properties=net_props,
        runtime_props={
            'resource_id': net_props['resource_id'],
            'network': net_props['network']
        }
    )
    rels = [
        MagicMock(
            name='network1',
            target=_net_ctx,
            type_hierarchy=[
                'cloudify.vcloud.port_connected_to_network',
                'cloudify.relationships.connected_to'
            ]
        ),
    ]
    _ctx = create_ctx(
        node_id='external_proxy',
        node_type=[
            'cloudify.nodes.Port',
            'cloudify.vcloud.nodes.Port'
        ],
        node_properties=port_props,
        relationships=rels
    )
    current_ctx.set(_ctx)
    creation_validation(ctx=_ctx)
    assert _ctx.instance.runtime_properties['network'] == 'foo-bar'
    assert _ctx.instance.runtime_properties['port']['ip_address'] == \
           '10.10.10.1'
