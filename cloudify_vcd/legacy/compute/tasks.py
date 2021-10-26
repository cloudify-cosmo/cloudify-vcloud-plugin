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

from cloudify.exceptions import OperationRetry

from vcd_plugin_sdk.resources.vapp import VCloudVM
from cloudify_common_sdk.utils import (
    get_ctx_instance,
    skip_creative_or_destructive_operation as skip)

from .. import decorators
from ... import vapp_tasks
from ..utils import VM_NIC_REL
from ...utils import (
    get_last_task,
    find_rels_by_type,
    check_if_task_successful)


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def create_server(vm_client, ctx, **_):
    if not skip(type(vm_client),
                vm_client.name,
                ctx,
                exists=vm_client.exists,
                create_operation=True):
        return vapp_tasks._create_vm(
            vm_external=False,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc_name,
            vm_config=vm_client.vapp_object.kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx)


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def configure_server(vm_client, ctx, **_):
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
def stop_server(vm_client, ctx, **_):
    return vapp_tasks._stop_vm(
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
    if not skip(type(vm_client),
                vm_client.name,
                exists=vm_client.exists,
                delete_operation=True):
        return vapp_tasks._delete_vm(
            vm_external=False,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc,
            vm_config=vm_client.kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx)


@decorators.with_port_resource()
def port_creation_validation(*_, **__):
    pass


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def preconfigure_nic(vm_client, ctx, **kwargs):
    for port_ctx in find_rels_by_type(get_ctx_instance(), VM_NIC_REL):
        resource, result = vapp_tasks._add_network(
            nic_config=port_ctx.instance.runtime_properties['port'],
            nic_ctx=port_ctx,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc,
            vm_config=vm_client.kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx,
            **kwargs)
        last_task = get_last_task(result)
        if not check_if_task_successful(resource, last_task):
            port_ctx.instance.runtime_properties['__RETRY_BAD_REQUEST'] = \
                True
            raise OperationRetry('Pending for operation completion.')


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def postconfigure_nic(vm_client, ctx, **kwargs):
    for port_ctx in find_rels_by_type(get_ctx_instance(), VM_NIC_REL):
        resource, result = vapp_tasks._add_nic(
            nic_config=port_ctx.instance.runtime_properties['port'],
            nic_ctx=port_ctx,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc,
            vm_config=vm_client.kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx,
            **kwargs)
        last_task = get_last_task(result)
        if not check_if_task_successful(resource, last_task):
            port_ctx.instance.runtime_properties['__RETRY_BAD_REQUEST'] = \
                True
            raise OperationRetry('Pending for operation completion.')


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def unlink_nic(vm_client, ctx, **kwargs):
    for port_ctx in find_rels_by_type(get_ctx_instance(), VM_NIC_REL):
        resource, result = vapp_tasks._delete_nic(
            nic_config=port_ctx.instance.runtime_properties['port'],
            nic_ctx=port_ctx,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc,
            vm_config=vm_client.kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx,
            **kwargs)
        last_task = get_last_task(result)
        if not check_if_task_successful(resource, last_task):
            port_ctx.instance.runtime_properties['__RETRY_BAD_REQUEST'] = \
                True
            raise OperationRetry('Pending for operation completion.')
