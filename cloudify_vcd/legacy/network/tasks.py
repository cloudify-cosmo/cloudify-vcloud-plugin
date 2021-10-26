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


from cloudify.exceptions import NonRecoverableError

from vcd_plugin_sdk.resources.network import VCloudNetwork
from cloudify_common_sdk.utils import \
    skip_creative_or_destructive_operation as skip

from .. import decorators
from ... import network_tasks


class MissingGateway(NonRecoverableError):
    pass


@decorators.with_vcd_client()
@decorators.with_network_resource()
@decorators.with_gateway_resource()
def create_network(network_client, gateway_client, ctx, **_):
    if network_client.network_type == 'routed_vdc_network' and \
            not gateway_client.gateway:
        raise MissingGateway(
            'The provided gateway {} does not exist.'.format(
                gateway_client.name))
    if not skip(network_client.network_type,
                network_client.name,
                ctx,
                exists=network_client.exists,
                create_operation=True):
        return network_tasks._create_network(
            external_network=False,
            network_id=network_client.name,
            network_client=network_client.connection,
            network_vdc=network_client.vdc_name,
            network_config=network_client.kwargs,
            network_class=VCloudNetwork,
            ctx=ctx)


@decorators.with_vcd_client()
@decorators.with_network_resource()
def delete_network(network_client, ctx, **_):
    if not skip(network_client.network_type,
                network_client.name,
                ctx,
                exists=network_client.exists,
                delete_operation=True):
        return network_tasks._delete_network(
            external_network=False,
            network_id=network_client.name,
            network_client=network_client.connection,
            network_vdc=network_client.vdc_name,
            network_config=network_client.kwargs,
            network_class=VCloudNetwork,
            ctx=ctx)
