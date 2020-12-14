
from cloudify import ctx

from .utils import expose_props
from .decorators import resource_operation
from vcd_plugin_sdk.exceptions import VCloudSDKException


@resource_operation
def configure_gateway(_,
                      gateway_id,
                      gateway_client,
                      gateway_vdc,
                      gateway_config,
                      gateway_class,
                      __,
                      **___):
    return gateway_class(
        gateway_id, gateway_client, gateway_vdc, gateway_config), None


@resource_operation
def delete_gateway(_,
                   gateway_id,
                   gateway_client,
                   gateway_vdc,
                   gateway_config,
                   gateway_class,
                   __,
                   **___):
    return gateway_class(
        gateway_id, gateway_client, gateway_vdc, gateway_config), None


@resource_operation
def create_firewall_rules(_,
                          __,
                          ___,
                          ____,
                          firewall_config,
                          _____,
                          firewall_ctx,
                          _______,
                          gateway_id,
                          gateway_client,
                          gateway_vdc,
                          ________,
                          gateway_class,
                          gateway_config,
                          **_________):

    gateway = gateway_class(
        gateway_id, gateway_client, gateway_vdc, gateway_config)
    firewall_rules = {
        'rules': {}
    }
    for firewall_rule_name, firewall_rule_config in firewall_config.items():
        result = gateway.create_firewall_rule(
            firewall_rule_name, **firewall_rule_config)
        firewall_rules['rules'].update(
            {
                result['Name']: result
            }
        )
    expose_props('create', gateway, firewall_rules, _ctx=firewall_ctx)
    return gateway, None


@resource_operation
def delete_firewall_rules(_,
                          __,
                          ___,
                          ____,
                          _____,
                          ______,
                          firewall_ctx,
                          _______,
                          gateway_id,
                          gateway_client,
                          gateway_vdc,
                          ________,
                          gateway_class,
                          gateway_config,
                          **_________):

    gateway = gateway_class(
        gateway_id, gateway_client, gateway_vdc, gateway_config)

    firewall_rules = \
        firewall_ctx.instance.runtime_properties.get('rules')
    for firewall_rule_name, firewall_rule_config in firewall_rules.items():
        try:
            gateway.delete_firewall_rule(
                firewall_rule_name, int(firewall_rule_config.get('Id')))
        except VCloudSDKException:
            ctx.logger.error(
                'Attempted to delete fire rule {r}, '
                'but the resource was not found.'.format(
                    r=firewall_rule_name))

    return gateway, None


@resource_operation
def create_static_routes(_,
                         __,
                         ___,
                         ____,
                         static_routes_config,
                         _____,
                         ______,
                         _______,
                         gateway_id,
                         gateway_client,
                         gateway_vdc,
                         ________,
                         gateway_class,
                         _________,
                         **__________):

    gateway = gateway_class(
        gateway_id, gateway_client, gateway_vdc)
    for static_route in static_routes_config:
        gateway.add_static_route(static_route)
    return gateway, None


@resource_operation
def delete_static_routes(_,
                         __,
                         ___,
                         ____,
                         static_routes_config,
                         _____,
                         ______,
                         _______,
                         gateway_id,
                         gateway_client,
                         gateway_vdc,
                         ________,
                         gateway_class,
                         _________,
                         **__________):

    gateway = gateway_class(
        gateway_id, gateway_client, gateway_vdc)
    for static_route in static_routes_config:
        try:
            gateway.delete_static_route(static_route)
        except VCloudSDKException:
            ctx.logger.error(
                'Attempted to delete static route {r}, '
                'but the resource was not found.'.format(r=static_route))

    return gateway, None


@resource_operation
def create_dhcp_pools(_,
                      __,
                      ___,
                      ____,
                      dhcp_pool_config,
                      _____,
                      ______,
                      _______,
                      gateway_id,
                      gateway_client,
                      gateway_vdc,
                      ________,
                      gateway_class,
                      _________,
                      **__________):

    gateway = gateway_class(
        gateway_id, gateway_client, gateway_vdc)
    dhcp_pools = {'pools': {}}
    for pool_definition in dhcp_pool_config:
        result = gateway.add_dhcp_pool(pool_definition)
        ctx.logger.info('result {}'.format(result))
        dhcp_pools['pools'].update(
            {
                result['ID']: result
            }
        )
    return gateway, None


@resource_operation
def delete_dhcp_pools(_,
                      __,
                      ___,
                      ____,
                      dhcp_pool_config,
                      _____,
                      ______,
                      _______,
                      gateway_id,
                      gateway_client,
                      gateway_vdc,
                      ________,
                      gateway_class,
                      _________,
                      **__________):
    gateway = gateway_class(
        gateway_id, gateway_client, gateway_vdc)
    for pool_definition in dhcp_pool_config:
        try:
            gateway.delete_dhcp_pool(pool_definition)
        except VCloudSDKException:
            ctx.logger.error(
                'Attempted to delete dhcp pool {p}, '
                'but the resource was not found.'.format(p=pool_definition))
    return gateway, None


@resource_operation
def create_nat_rules(_,
                     __,
                     ___,
                     ____,
                     nat_rule_config,
                     _____,
                     nat_rule_ctx,
                     _______,
                     gateway_id,
                     gateway_client,
                     gateway_vdc,
                     ________,
                     gateway_class,
                     _________,
                     **__________):

    gateway = gateway_class(
        gateway_id, gateway_client, gateway_vdc)
    nat_rules = {'rules': {}}
    for nat_rule_def in nat_rule_config:
        result = gateway.create_nat_rule(nat_rule_def)
        nat_rules['rules'].update(
            {
                result['ID']: result
            }
        )
        expose_props('create', gateway, nat_rules, _ctx=nat_rule_ctx)
    return gateway, None


@resource_operation
def delete_nat_rules(_,
                     __,
                     ___,
                     ____,
                     _____,
                     ______,
                     nat_rule_ctx,
                     _______,
                     gateway_id,
                     gateway_client,
                     gateway_vdc,
                     ________,
                     gateway_class,
                     _________,
                     **__________):
    gateway = gateway_class(
        gateway_id, gateway_client, gateway_vdc)
    nat_rules = nat_rule_ctx.instance.runtime_properties.get('rules')
    for nat_rule_id, _ in nat_rules.items():
        try:
            gateway.delete_nat_rule(nat_rule_id)
        except VCloudSDKException:
            ctx.logger.error(
                'Attempted to delete nat rule {r}, '
                'but the resource was not found.'.format(r=nat_rule_id))
    return gateway, None
