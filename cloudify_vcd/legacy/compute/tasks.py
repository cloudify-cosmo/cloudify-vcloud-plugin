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
from cloudify_common_sdk.utils import \
    skip_creative_or_destructive_operation as skip

from .. import decorators
from ... import vapp_tasks


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def create_server(vm_client, ctx, **_):
    exists = vm_client.get()
    if not skip(type(vm_client), vm_client.name, exists):
        return vapp_tasks._create_vm(
            vm_external=False,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc_name,
            vm_config=vm_client.kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx)


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def configure_server(vm_client, ctx, **_):
    exists = vm_client.get()
    if not skip(type(vm_client), vm_client.name, exists):
        return vapp_tasks._configure_vm(
            vm_external=False,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc_name,
            vm_config=vm_client.kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx)


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def start_server(vm_client, ctx, **_):
    exists = vm_client.get()
    if not skip(type(vm_client), vm_client.name, exists):
        return vapp_tasks._start_vm(
            vm_external=False,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc,
            vm_config=vm_client.kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx)


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def delete_server(vm_client, ctx, **_):
    exists = vm_client.get()
    if not skip(type(vm_client), vm_client.name, exists):
        return vapp_tasks._delete_vm(
            vm_external=False,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc,
            vm_config=vm_client.kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx)


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def stop_server(vm_client, ctx, **_):
    exists = vm_client.get()
    if not skip(type(vm_client), vm_client.name, exists):
        return vapp_tasks._stop_vm(
            vm_external=False,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc,
            vm_config=vm_client.kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx)


def configure_nic(ctx, **_):
    ctx.logger.info('Storing')
    return vapp_tasks._configure_nic(
        nic_config=ctx.node.properties['port'], nic_ctx=ctx)
