
from .decorators import resource_operation
from .utils import (
    find_resource_id_from_relationship_by_type)

REL_VAPP_NETWORK = 'cloudify.relationships.vcloud.vapp_connected_to_network'


@resource_operation
def create_vapp(_,
                vapp_id,
                vapp_client,
                vapp_vdc,
                vapp_config,
                vapp_class,
                vapp_ctx,
                **___):

    network = find_resource_id_from_relationship_by_type(
        vapp_ctx.instance, REL_VAPP_NETWORK)
    if network and 'network' not in vapp_config:
        vapp_config['network'] = network

    vapp = vapp_class(
        vapp_id,
        vapp_client,
        vapp_vdc,
        kwargs=vapp_config
    )
    return vapp, None


@resource_operation
def stop_vapp(_,
              vapp_id,
              vapp_client,
              vapp_vdc,
              vapp_config,
              vapp_class,
              __,
              **___):
    vapp = vapp_class(
        vapp_id,
        vapp_client,
        vapp_vdc,
        kwargs=vapp_config
    )
    vapp.undeploy()
    return vapp, None


@resource_operation
def delete_vapp(_,
                vapp_id,
                vapp_client,
                vapp_vdc,
                vapp_config,
                vapp_class,
                __,
                **___):
    vapp = vapp_class(
        vapp_id,
        vapp_client,
        vapp_vdc,
        kwargs=vapp_config
    )
    vapp.delete()
    return vapp, None
