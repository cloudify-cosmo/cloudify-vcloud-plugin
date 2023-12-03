
from .decorators import resource_operation
from .utils import find_resource_id_from_relationship_by_type

REL_NETWORK_GW = 'cloudify.relationships.vcloud.network_connected_to_gateway'

NETWORK_TYPES = {
    'cloudify.nodes.vcloud.RoutedVDCNetwork': 'routed_vdc_network',
    'cloudify.nodes.vcloud.DirectlyConnectedVDCNetwork':
        'directly_connected_vdc_network',
    'cloudify.nodes.vcloud.IsolatedVDCNetwork': 'isolated_vdc_network',
}


def get_network_type(types):
    for node_type in types:
        network_type = NETWORK_TYPES.get(node_type)
        if network_type:
            return network_type


@resource_operation
def create_network(external_network,
                   network_id,
                   network_client,
                   network_vdc,
                   network_config,
                   network_class,
                   ctx,
                   **__):

    try:
        network = find_resource_id_from_relationship_by_type(
            ctx.instance, REL_NETWORK_GW)
    except AttributeError:
        network = None

    if network and 'network_name' not in network_config:
        network_config['network_name'] = network

    network = network_class(
        network_id,
        network_type,
        network_client,
        network_vdc,
        kwargs=network_config)
    if external_network:
        return network, None
    last_task = network.create()
    return network, last_task


@resource_operation
def delete_network(external_network,
                   network_id,
                   network_client,
                   network_vdc,
                   network_config,
                   network_class,
                   ctx,
                   **___):
    network = network_class(
        network_id,
        get_network_type(ctx.node.type_hierarchy),
        network_client,
        network_vdc,
        kwargs=network_config)
    if external_network:
        return network, None
    last_task = network.delete()
    return network, last_task
