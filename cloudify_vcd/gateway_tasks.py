
from .decorators import resource_operation
from .utils import expose_props


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
    expose_props('create', expose_props(firewall_rules))
    return gateway, None


@resource_operation
def delete_firewall_rules(_,
                          __,
                          ___,
                          ____,
                          _____,
                          ______,
                          _______,
                          firewall_ctx,
                          gateway_id,
                          gateway_client,
                          gateway_vdc,
                          ________,
                          gateway_class,
                          _________,
                          **__________):

    gateway = gateway_class(
        gateway_id, gateway_client, gateway_vdc)

    firewall_rules = \
        firewall_ctx.instance.runtime_properties.get('rules')
    for firewall_rule_name, firewall_rule_config in firewall_rules.items():
        gateway.delete_firewall_rule(firewall_rule_name,
                                     firewall_rule_config.get('Id'))
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
        gateway.add_static_route(**static_route)
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
        gateway.delete_static_route(**static_route)
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
    for pool_definition in dhcp_pool_config.items():
        result = gateway.add_dhcp_pool(**pool_definition)
        dhcp_pools['pools'].update(
            {
                result['Id']: result
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
    for pool_definition in dhcp_pool_config.items():
        gateway.delete_dhcp_pool(**pool_definition)
    return gateway, None


@resource_operation
def create_nat_rules(_,
                     __,
                     ___,
                     ____,
                     nat_rule_config,
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
    nat_rules = {'rules': {}}
    for nat_rule_def in nat_rule_config.items():
        result = gateway.create_nat_rule(**nat_rule_def)
        nat_rules['rules'].update(
            {
                result['Id']: result
            }
        )
        expose_props('create', expose_props(nat_rules))
    return gateway, None


@resource_operation
def delete_nat_rules(_,
                     __,
                     ___,
                     ____,
                     _____,
                     ______,
                     _______,
                     nat_rule_ctx,
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
        gateway.delete_nat_rule(**nat_rule_id)
    return gateway, None
