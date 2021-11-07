# Copyright (c) 2014-21 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ipaddress
from copy import deepcopy
from tempfile import NamedTemporaryFile

from ..utils import (
    find_rels_by_type,
    find_resource_id_from_relationship_by_type)

from vcd_plugin_sdk.resources.vapp import VCloudVM
from vcd_plugin_sdk.connection import VCloudConnect
from vcd_plugin_sdk.resources.network import VCloudNetwork, VCloudGateway

from cloudify import ctx as ctx_from_import
from cloudify.exceptions import NonRecoverableError
from cloudify_common_sdk.utils import (
    get_ctx_node,
    get_ctx_instance,
    get_deployment_dir
)


OLD_NETWORK_KEYS = [
    'dns',
    'name',
    'dhcp',
    'netmask',
    'gateway_ip',
    'dns_suffix',
    'static_range',
    'edge_gateway'
]
OLD_PORT_KEYS = [
    'network',
    'mac_address',
    'primary_interface',
    'ip_allocation_mode'
]
OLD_VM_KEYS = [
    'name',
    'hardware',
    'guest_customization',
]
PORT_NET_REL = 'cloudify.vcloud.port_connected_to_network'
VM_NIC_REL = 'cloudify.vcloud.server_connected_to_port'


class RequiredClientKeyMissing(NonRecoverableError):
    def __init__(self, key, *args, **kwargs):
        msg = 'Required vcloud config key "{}" not provided.'.format(key)
        super().__init__(msg, *args, **kwargs)


def get_function_return(func_ret):
    if isinstance(func_ret, tuple) and len(func_ret) == 2:
        return func_ret
    return None, None


def get_vcloud_cx(client_config, logger):
    client_config = deepcopy(client_config)
    for bad, good in [('username', 'user'),
                      ('ssl_verify', 'verify_ssl_certs')]:
        if bad in client_config:
            logger.warning(
                'The vcloud_config contains the key "{}". '
                'This is an invalid key. The correct key is "{}".'.format(
                    good, bad))
            client_config[good] = client_config.pop(bad)

    for key in ['user', 'password', 'org']:
        if key not in client_config:
            raise RequiredClientKeyMissing(key)

    credentials = {
        'org': client_config.pop('org'),
        'user': client_config.pop('user'),
        'password': client_config.pop('password')
    }
    new_client_config = {'uri': client_config.pop('url')}

    if 'api_version' in client_config:
        new_client_config['api_version'] = client_config.pop('api_version')

    if 'verify_ssl_certs' in client_config:
        new_client_config['verify_ssl_certs'] = client_config.pop(
            'verify_ssl_certs')

    if 'log_file' not in new_client_config:
        new_temp = NamedTemporaryFile(
            dir=get_deployment_dir(ctx_from_import.deployment.id))
        new_client_config['log_file'] = new_temp.name

    # TODO: Figure out what to do with the rest of the stuff in client_config.
    return VCloudConnect(logger, new_client_config, credentials)


def get_network_client(network, vcloud_cx, vcloud_config, ctx, **_):
    """
    Take the network configuration from legacy node type and convert it to
    something that the vcd_plugin_sdk objects can understand.

    :param network: from ctx.node.properties['network'] or
        operation inputs['network']
    :param vcloud_cx: VCloudConnect from with_vcloud_client decorator.
    :param vcloud_config: from ctx.node.properties['vcloud_config'] or
        operation inputs['vcloud_config']
    :param ctx:
    :param kwargs:
    :return:
    """

    _ctx_node = get_ctx_node(ctx)
    _ctx_instance = get_ctx_instance(ctx)

    network_type = 'directly_connected_vdc_network'

    # if 'edge_gateway' in vcloud_config:
    #     network['gateway_name'] = vcloud_config['edge_gateway']
    #     network_type = 'routed_vdc_network'
    # else:
    #     network_type = 'isolated_vdc_network'

    tasks = _ctx_instance.runtime_properties.get('__TASKS', [])
    if 'name' in network:
        network_name = network.pop('name')
    elif 'resource_id' in _ctx_instance.runtime_properties:
        network_name = _ctx_instance.runtime_properties['resource_id']
    else:
        network_name = _ctx_node.properties.get(
            'resource_id', _ctx_instance.id)
    if network_type == 'directly_connected_vdc_network':
        network = {
            'parent_network_name': network.get('parent_network_name', None)
        }
    network = convert_routed_network_config(network)

    _ctx_instance.runtime_properties['resource_id'] = network_name
    _ctx_instance.runtime_properties['network'] = network

    new_network_config = {
        'network_name': network_name,
        'network_type': network_type,
        'connection': vcloud_cx,
        'vdc_name': vcloud_config.get('vdc'),
        'kwargs': network,
        'tasks': tasks
    }
    return VCloudNetwork(**new_network_config)


def get_port_config(port, ctx, **kwargs):
    """
    :param port:
    :param vcloud_cx:
    :param vcloud_config:
    :param ctx:
    :param kwargs:
    :return:
    """

    _node_instance = get_ctx_instance(ctx)

    if 'network' in port:
        network = port.pop('network')
    else:
        network = find_resource_id_from_relationship_by_type(
            _node_instance, PORT_NET_REL)

    port = convert_port_config(port)
    if 'network_name' not in port:
        port['network_name'] = network
    if 'is_connected' not in port:
        port['is_connected'] = True
    _node_instance.runtime_properties['network'] = network
    _node_instance.runtime_properties['port'] = port


def get_gateway_client(vcloud_cx, vcloud_config, ctx, **_):
    _ctx_instance = get_ctx_instance(ctx)
    tasks = _ctx_instance.runtime_properties.get('__TASKS', [])

    if 'edge_gateway' in vcloud_config:
        return VCloudGateway(
            vcloud_config['edge_gateway'],
            connection=vcloud_cx,
            vdc_name=vcloud_config.get('vdc'),
            tasks=tasks
        )


def get_vm_client(server, vcloud_cx, vcloud_config, ctx):
    _ctx_node = get_ctx_node(ctx)
    _ctx_instance = get_ctx_instance(ctx)
    name = None
    if 'name' in server:
        name = server.pop('name')
    if not name and 'name' in _ctx_instance.runtime_properties:
        name = _ctx_instance.runtime_properties['name']
    if not name:
        server_from_props = _ctx_node.properties.get('server')
        name = server_from_props.get('name')
    if not name:
        name = _ctx_node.properties.get('resource_id', _ctx_instance.id)
    if not name and 'resource_id' in _ctx_instance.runtime_properties:
        name = _ctx_instance.runtime_properties['resource_id']
    tasks = _ctx_instance.runtime_properties.get('__TASKS', [])
    convert_vm_config(server)
    get_server_network(server, _ctx_node, _ctx_instance)
    _ctx_instance.runtime_properties['resource_id'] = name
    _ctx_instance.runtime_properties['server'] = server
    ctx.logger.info('We are getting this name: {}'.format(name))
    # TODO: Change vcloud VM name to host name guest customization pizazz.
    return VCloudVM(name,
                    name,
                    connection=vcloud_cx,
                    vdc_name=vcloud_config.get('vdc'),
                    kwargs={},
                    vapp_kwargs=server,
                    tasks=tasks)


def get_server_network(server, _ctx_node, _ctx_instance):
    rel = None
    server_network_adapter = 'VMXNET3'

    if 'network' not in server and \
            'management_network_name' in _ctx_node.properties:
        server['network'] = _ctx_node.properties['management_network_name']
    elif 'network' not in server:
        for rel in find_rels_by_type(_ctx_instance, VM_NIC_REL):
            if rel.target.node.properties['port'].get('primary_interface'):
                break
        if rel:
            server['network'] = rel.target.instance.runtime_properties.get(
                'network_name')

    if 'network_adapter_type' not in server and rel:
        server['network_adapter_type'] = \
            rel.target.instance.runtime_properties['port'].get(
                'adapter_type', server_network_adapter)
    elif 'network_adapter_type' not in server:
        server['network_adapter_type'] = server_network_adapter

    if 'ip_address' not in server and rel:
        ip_address = rel.target.instance.runtime_properties['port'].get(
            'ip_address')
        if ip_address:
            server['ip_address'] = ip_address


def convert_routed_network_config(config):

    if 'network_cidr' not in config:
        cidr = get_network_cidr(config)
        if cidr:
            config['network_cidr'] = cidr

    if 'ip_range_start' not in config or 'ip_range_end' not in config:
        ip_range_start, ip_range_end = get_ip_range(config)
        if ip_range_start:
            config['ip_range_start'] = ip_range_start.compressed
        if ip_range_end:
            config['ip_range_end'] = ip_range_end.compressed

    if 'dns' in config:
        primary_ip, secondary_ip = get_dns_ips(config['dns'])
        config['primary_dns_ip'] = primary_ip
        config['secondary_dns_ip'] = secondary_ip

    for key in OLD_NETWORK_KEYS:
        config.pop(key, None)

    return config


def get_start_end_ip_config(config=None):
    start = None
    end = None
    if config:
        start, end = config.split('-')
        start = ipaddress.IPv4Address(start)
        end = ipaddress.IPv4Address(end)
    return start, end


def get_gateway_ip(config):
    gateway_ip = config.get('gateway_ip')
    if gateway_ip:
        return ipaddress.IPv4Address(gateway_ip)


def get_ip_range(config):
    start_static, end_static = get_start_end_ip_config(
        config.get('static_range'))
    start_dhcp, end_dhcp = get_start_end_ip_config(config.get('dhcp_range'))
    start_list = sorted(
        [n for n in [start_static, start_dhcp] if n])
    if start_list:
        start = start_list[-1]
    else:
        return None, None
    end_list = sorted([n for n in [end_static, end_dhcp] if n])
    if end_list:
        end = end_list[-1]
    else:
        return None, None
    return start, end


def get_network_cidr(config):
    """
    A naive way to generate a CIDR from old style network configuration.
    :param config:
    :return:
    """
    start, end = get_ip_range(config)
    gateway_ip = get_gateway_ip(config)
    netmask = config.get('netmask')
    if netmask:
        netmask = ipaddress.IPv4Address('0.0.0.0/{}'.format(netmask))
    if gateway_ip:
        start = gateway_ip
    ctx_from_import.logger.info(
        'Using these IPs for CIDR: {} {}'.format(start, end))
    if not start or not end:
        return None
    ip_range = [addr for addr in ipaddress.summarize_address_range(start, end)]
    if len(ip_range) >= 1:
        if netmask:
            return '{}/{}'.format(
                ip_range[0].network_address, netmask.prefixlen)
        return ip_range[0].compressed


def get_dns_ips(ips):
    if len(ips) > 1:
        return ips[0], ips[1]
    return ips[0], None


def convert_port_config(config):
    """Convert something like this:
    port:
        network: { get_input: RSP_VRS2_APP_EXT_PROXY_network_name }
        ip_allocation_mode: manual
        ip_address: { get_input: RSP_VRS2_APP_EXT_PROXY }
        primary_interface: false
    To this:
        adapter_type: 'VMXNET3'
        is_primary: false
        is_connected: false
        ip_address_mode: 'MANUAL'
        ip_address: '192.179.2.2'
    :param config:
    :return:
    """

    if 'ip_allocation_mode' in config:
        config['ip_address_mode'] = config.pop('ip_allocation_mode').upper()

    if 'primary_interface' in config:
        config['is_primary'] = config.pop('primary_interface')

    for key in OLD_PORT_KEYS:
        config.pop(key, None)

    return config


def convert_vapp_config(config):
    return {
        'fence_mode': config.get('fence_mode', 'direct'),
        'accept_all_eulas': config.get('accept_all_eulas', True)
    }


def convert_vm_config(config):
    if 'hardware' in config:
        if 'memory' in config['hardware']:
            config['memory'] = config['hardware']['memory']
        if 'cpus' in config['hardware']:
            config['cpus'] = config['hardware']['cpu']
    if 'guest_customization' in config:
        if 'admin_password' in config['guest_customization']:
            config['password'] = \
                config['guest_customization']['admin_password']
        if 'computer_name' in config:
            config['hostname'] = \
                config['guest_customization']['computer_name']

    config.update(convert_vapp_config(config))

    for key in OLD_VM_KEYS:
        config.pop(key, None)
