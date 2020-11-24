from pyvcloud.vcd.exceptions import (
    BadRequestException,
    MissingLinkException,
    OperationNotSupportedException)

from cloudify import ctx
from cloudify.exceptions import OperationRetry, NonRecoverableError

from .decorators import resource_operation
from .network_tasks import get_network_type
from .utils import (
    cannot_power_off,
    find_rel_by_type,
    vcd_unresolved_vm,
    vcd_already_exists,
    find_resource_id_from_relationship_by_type)

REL_VAPP_NETWORK = 'cloudify.relationships.vcloud.vapp_connected_to_network'
REL_VM_NETWORK = 'cloudify.relationships.vcloud.vm_connected_to_network'
REL_VM_VAPP = 'cloudify.relationships.vcloud.vm_contained_in_vapp'
REL_NIC_NETWORK = 'cloudify.relationships.vcloud.nic_connected_to_network'
REL_VM_NIC = 'cloudify.relationships.vcloud.vm_connected_to_nic'


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

    return vapp_class(
        vapp_id,
        vapp_client,
        vapp_vdc,
        kwargs=vapp_config
    ), None


@resource_operation
def stop_vapp(vapp_ext,
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
    if not vapp_ext:
        vapp.undeploy()
    return vapp, None


@resource_operation
def delete_vapp(vapp_ext,
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
    if not vapp_ext:
        vapp.delete()
    return vapp, None


@resource_operation
def create_vm(vm_external,
              vm_id,
              vm_client,
              vm_vdc,
              vm_config,
              vm_class,
              vm_ctx):
    vapp_name = find_resource_id_from_relationship_by_type(
        vm_ctx.instance, REL_VM_VAPP)  # or vapp_id
    network = find_rel_by_type(
        vm_ctx.instance, REL_VM_NETWORK)
    if network:
        vm_config['network'] = vm_config.get(
            'network',
            network.target.instance.runtime_properties.get('resource_id'))

    vm = vm_class(
        vm_id,
        vapp_name,
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    )
    if vm_external:
        return vm, None
    if network:
        network_type = get_network_type(network.target.node.type_hierarchy)
        if not vm.check_network(vm_config['network'], network_type):
            raise OperationRetry(
                'Waiting on the network {n} to be ready'.format(
                    n=vm_config['network']))
    try:
        last_task = vm.instantiate_vapp()
    except BadRequestException as e:
        if not vcd_already_exists(e) and not vm_external:
            raise
        else:
            vm.logger.warn('The vm {name} unexpectedly exists.'.format(
                name=vm.name))
            last_task = None
    vm_ctx.instance.runtime_properties['__VM_CREATE_VAPP'] = True
    return vm, last_task


@resource_operation
def configure_vm(_,
                 vm_id,
                 vm_client,
                 vm_vdc,
                 vm_config,
                 vm_class,
                 vm_ctx):
    vapp_name = find_resource_id_from_relationship_by_type(
        vm_ctx.instance, REL_VM_VAPP)
    return vm_class(
        vm_id,
        vapp_name,
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    ), None


@resource_operation
def start_vm(vm_external,
             vm_id,
             vm_client,
             vm_vdc,
             vm_config,
             vm_class,
             vm_ctx):
    vapp_name = find_resource_id_from_relationship_by_type(
        vm_ctx.instance, REL_VM_VAPP)
    vm = vm_class(
        vm_id,
        vapp_name,
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    )
    if vm_external:
        return vm, None
    last_task = vm.power_on()
    return vm, last_task


@resource_operation
def stop_vm(vm_external,
            vm_id,
            vm_client,
            vm_vdc,
            vm_config,
            vm_class,
            vm_ctx):
    vapp_name = find_resource_id_from_relationship_by_type(
        vm_ctx.instance, REL_VM_VAPP)
    vm = vm_class(
        vm_id,
        vapp_name,
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    )
    if vm_external:
        return vm, None
    try:
        last_task = vm.power_off()
    except (MissingLinkException, OperationNotSupportedException) as e:
        if not vcd_unresolved_vm(e) and not cannot_power_off(e):
            raise
        last_task = None
    return vm, last_task


@resource_operation
def delete_vm(vm_external,
              vm_id,
              vm_client,
              vm_vdc,
              vm_config,
              vm_class,
              vm_ctx):
    vapp_name = find_resource_id_from_relationship_by_type(
        vm_ctx.instance, REL_VM_VAPP)
    vm = vm_class(
        vm_id,
        vapp_name,
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    )
    if vm_external:
        return vm, None
    try:
        last_task = vm.undeploy()
    except (MissingLinkException, OperationNotSupportedException) as e:
        if not vcd_unresolved_vm(e) and not cannot_power_off(e):
            raise
        last_task = None
    if vm_ctx.instance.runtime_properties.get('__VM_CREATE_VAPP'):
        vm.vapp_object.delete_vms(vm_id)
        last_task = vm.vapp_object.delete()
    return vm, last_task


@resource_operation
def configure_nic(_,
                  __,
                  ___,
                  ____,
                  nic_config,
                  _____,
                  nic_ctx):
    NIC_NETWORK = find_resource_id_from_relationship_by_type(
        nic_ctx.instance, REL_NIC_NETWORK)
    if NIC_NETWORK:
        nic_ctx.instance.runtime_properties['network'] = NIC_NETWORK
    elif not nic_config['network_name']:
        raise NonRecoverableError(
            'No relationship of type {t} was provided and network_name is '
            'not in the resource config.'.format(t=REL_NIC_NETWORK))
    return None, None


@resource_operation
def add_nic(_,
            __,
            ___,
            ____,
            nic_config,
            _____,
            ______,
            _______,
            vm_id,
            vm_client,
            vm_vdc,
            vm_config,
            vm_class,
            vm_ctx,
            **________):
    vapp_name = find_resource_id_from_relationship_by_type(
        vm_ctx.instance, REL_VM_VAPP)
    vm = vm_class(
        vm_id,
        vapp_name,
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    )
    last_task = vm.add_nic(**nic_config)
    return vm, last_task


@resource_operation
def delete_nic(_,
               __,
               ___,
               ____,
               nic_config,
               _____,
               ______,
               _______,
               vm_id,
               vm_client,
               vm_vdc,
               vm_config,
               vm_class,
               vm_ctx,
               **________):
    vapp_name = find_resource_id_from_relationship_by_type(
        vm_ctx.instance, REL_VM_VAPP)
    vm = vm_class(
        vm_id,
        vapp_name,
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    )
    for nic in vm.nics:
        if nic['ip_address'] == nic_config['ip_address']:
            last_task = vm.delete_nic(**nic_config)
            return vm, last_task
    ctx.logger.error(
        'The NIC {config} was not found, '
        'so we cannot remove it from the VM.'.format(config=nic_config))
    return None, None
