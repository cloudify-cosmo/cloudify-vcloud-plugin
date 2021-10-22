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

from vcd_plugin_sdk.resources.vapp import VCloudVM
from vcd_plugin_sdk.connection import VCloudConnect
from vcd_plugin_sdk.resources.network import VCloudNetwork, VCloudGateway

from cloudify.exceptions import NonRecoverableError
from cloudify_common_sdk.utils import (
    get_ctx_node,
    get_ctx_instance)


class RequiredClientKeyMissing(NonRecoverableError):
    def __init__(self, key, *args, **kwargs):
        msg = 'Required vcloud config key "{}" not provided.'.format(key)
        super().__init__(msg, *args, **kwargs)


def get_function_return(func_ret):
    if isinstance(func_ret, tuple) and len(func_ret) == 2:
        return func_ret
    return None, None


def get_vcloud_cx(client_config, logger):
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

    if 'edge_gateway' in vcloud_config:
        network_type = 'routed_vdc_network'
        network['gateway_name'] = vcloud_config['edge_gateway']
    else:
        network_type = 'isolated_vdc_network'

    tasks = _ctx_instance.runtime_properties.get('__TASKS', [])

    new_network_config = {
        'network_name': _ctx_node.properties.get(
            'resource_id', _ctx_instance.id),
        'network_type': network_type,
        'connection': vcloud_cx,
        'vdc_name': vcloud_config.get('vdc'),
        'kwargs': network,
        'tasks': tasks
    }

    return VCloudNetwork(**new_network_config)


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


def get_vm_client(vcloud_cx, vcloud_config, ctx):
    _ctx_node = get_ctx_node(ctx)
    _ctx_instance = get_ctx_instance(ctx)
    name = _ctx_node.properties.get('resource_id', _ctx_instance.id)
    return VCloudVM(name,
                    name,
                    connection=vcloud_cx,
                    vdc_name=vcloud_config.get('vdc'),
                    tasks=_ctx_instance.runtime_properties['__TASKS'])
