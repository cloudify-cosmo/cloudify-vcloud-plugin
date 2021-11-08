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

from copy import deepcopy

from cloudify.exceptions import OperationRetry

from vcd_plugin_sdk.resources.vapp import VCloudVM
from cloudify_common_sdk.utils import (
    get_ctx_instance,
    skip_creative_or_destructive_operation as skip)

from .. import decorators
from ... import vapp_tasks
from ..utils import VM_NIC_REL
from ...utils import (
    expose_props,
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
        vm_kwargs = deepcopy(vm_client.vapp_object.kwargs)
        if 'network' in vm_kwargs:
            del vm_kwargs['network']
            del vm_kwargs['network_adapter_type']
        resource, result = vapp_tasks._create_vm(
            vm_external=False,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc_name,
            vm_config=vm_kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx)
    else:
        resource = vm_client.vm
    ctx.logger.info('Logging resource object: {}'.format(resource))
    operation_name = ctx.operation.name.split('.')[-1]
    expose_props(operation_name,
                 vm_client,
                 _ctx=ctx,
                 legacy=True)


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def configure_server(vm_client, ctx, **_):
    resource, result = vapp_tasks._configure_vm(
        vm_external=False,
        vm_id=vm_client.name,
        vm_client=vm_client.connection,
        vm_vdc=vm_client.vdc_name,
        vm_config=vm_client.kwargs,
        vm_class=VCloudVM,
        vm_ctx=ctx)
    # operation_name = ctx.operation.name.split('.')[-1]
    # expose_props(operation_name,
    #              resource,
    #              _ctx=ctx,
    #              legacy=True)


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def start_server(vm_client, ctx, **_):
    resource, result = vapp_tasks._start_vm(
        vm_external=False,
        vm_id=vm_client.name,
        vm_client=vm_client.connection,
        vm_vdc=vm_client.vdc_name,
        vm_config=vm_client.kwargs,
        vm_class=VCloudVM,
        vm_ctx=ctx)
    operation_name = ctx.operation.name.split('.')[-1]
    expose_props(operation_name,
                 resource,
                 _ctx=ctx,
                 legacy=True)
    ctx.instance.runtime_properties['vcloud_vapp_name'] = \
        ctx.instance.runtime_properties.get('name')


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def stop_server(vm_client, ctx, **_):
    resource, result = vapp_tasks._stop_vm(
        vm_external=False,
        vm_id=vm_client.name,
        vm_client=vm_client.connection,
        vm_vdc=vm_client.vdc_name,
        vm_config=vm_client.kwargs,
        vm_class=VCloudVM,
        vm_ctx=ctx)
    operation_name = ctx.operation.name.split('.')[-1]
    expose_props(operation_name,
                 resource,
                 _ctx=ctx,
                 legacy=True)


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def delete_server(vm_client, ctx, **_):
    if not skip(type(vm_client),
                vm_client.name,
                exists=vm_client.exists,
                delete_operation=True):
        resource, result = vapp_tasks._delete_vm(
            vm_external=False,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc_name,
            vm_config=vm_client.kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx)
    else:
        resource = vm_client
    operation_name = ctx.operation.name.split('.')[-1]
    expose_props(operation_name,
                 resource,
                 _ctx=ctx,
                 legacy=True)


@decorators.with_port_resource()
def port_creation_validation(*_, **__):
    pass


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def preconfigure_nic(vm_client, ctx, server, **kwargs):
    for port_ctx in find_rels_by_type(get_ctx_instance(), VM_NIC_REL):
        resource, result = vapp_tasks._add_network(
            nic_config=port_ctx.target.instance.runtime_properties['port'],
            nic_ctx=port_ctx.target,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc_name,
            vm_config=server,
            vm_class=VCloudVM,
            vm_ctx=ctx,
            **kwargs)
        last_task = get_last_task(result)
        if not check_if_task_successful(resource, last_task):
            port_ctx.target.instance.runtime_properties['__RETRY_BAD_'
                                                        'REQUEST'] = \
                True
            raise OperationRetry('Pending for operation completion.')
        operation_name = ctx.operation.name.split('.')[-1]
        expose_props(operation_name,
                     resource,
                     _ctx=port_ctx.target,
                     legacy=True)


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def postconfigure_nic(vm_client, server, ctx, **kwargs):
    vm_id = vm_client.name
    if not vm_id:
        vm_id = ctx.node.properties.get('server', {}).get('name')
    ctx.logger.info('Preconfigure vm client name {}'.format(vm_id))
    ctx.logger.info('Preconfigure server {}'.format(server))
    for port_ctx in find_rels_by_type(get_ctx_instance(), VM_NIC_REL):
        # port = convert_nic_config(
        #     port_ctx.target.instance.runtime_properties['port'])
        resource, result = vapp_tasks._add_nic(
            nic_config=port_ctx.target.instance.runtime_properties['port'],
            nic_ctx=port_ctx.target,
            vm_id=vm_id,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc_name,
            vm_config=server,
            vm_class=VCloudVM,
            vm_ctx=ctx,
            **kwargs)
        last_task = get_last_task(result)
        if not check_if_task_successful(resource, last_task):
            port_ctx.target.instance.runtime_properties['__RETRY_BAD_'
                                                        'REQUEST'] = \
                True
            raise OperationRetry('Pending for operation completion.')
        operation_name = ctx.operation.name.split('.')[-1]
        expose_props(operation_name,
                     resource,
                     _ctx=port_ctx.target,
                     legacy=True)


@decorators.with_vcd_client()
@decorators.with_vm_resource()
def unlink_nic(vm_client, ctx, **kwargs):
    for port_ctx in find_rels_by_type(get_ctx_instance(), VM_NIC_REL):
        resource, result = vapp_tasks._delete_nic(
            nic_config=port_ctx.target.instance.runtime_properties['port'],
            nic_ctx=port_ctx.target,
            vm_id=vm_client.name,
            vm_client=vm_client.connection,
            vm_vdc=vm_client.vdc_name,
            vm_config=vm_client.kwargs,
            vm_class=VCloudVM,
            vm_ctx=ctx,
            **kwargs)
        last_task = get_last_task(result)
        if not check_if_task_successful(resource, last_task):
            port_ctx.target.instance.runtime_properties['__RETRY_BAD_'
                                                        'REQUEST'] = \
                True
            raise OperationRetry('Pending for operation completion.')
        operation_name = ctx.operation.name.split('.')[-1]
        expose_props(operation_name,
                     resource,
                     _ctx=port_ctx.target,
                     legacy=True)
