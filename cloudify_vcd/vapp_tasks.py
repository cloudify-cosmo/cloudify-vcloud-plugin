from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.exceptions import (
    BadRequestException,
    MissingLinkException,
    InvalidStateException,
    OperationNotSupportedException)

from cloudify import ctx
from cloudify.exceptions import OperationRetry, NonRecoverableError

from .decorators import resource_operation
from .network_tasks import get_network_type
from .utils import (
    bad_vm_name,
    cannot_power_off,
    find_rel_by_type,
    no_powered_on_vms,
    vcd_unresolved_vm,
    vcd_already_exists,
    expose_ip_property,
    find_resource_id_from_relationship_by_type)

REL_VAPP_NETWORK = 'cloudify.relationships.vcloud.vapp_connected_to_network'
REL_VM_NETWORK = 'cloudify.relationships.vcloud.vm_connected_to_network'
REL_VM_VAPP = 'cloudify.relationships.vcloud.vm_contained_in_vapp'
REL_NIC_NETWORK = 'cloudify.relationships.vcloud.nic_connected_to_network'
REL_VM_NIC = 'cloudify.relationships.vcloud.vm_connected_to_nic'
FENCE_MODE = ['isolated', 'direct', 'bridged', 'natRouted']


@resource_operation
def create_vapp(_,
                vapp_id,
                vapp_client,
                vapp_vdc,
                vapp_config,
                vapp_class,
                vapp_ctx,
                **___):
    """
    At the moment this function does nothing substantial.
    Creating vApps happens during VM create.

    :param _:
    :param vapp_id:
    :param vapp_client:
    :param vapp_vdc:
    :param vapp_config:
    :param vapp_class:
    :param vapp_ctx:
    :param ___: Unused kwargs.
    :return:
    """

    network = find_resource_id_from_relationship_by_type(
        vapp_ctx.instance, REL_VAPP_NETWORK)
    if network and 'network' not in vapp_config:
        vapp_config['network'] = network

    fence_mode = vapp_config.get('fence_mode')
    if fence_mode not in FENCE_MODE:
        raise NonRecoverableError(
            'The provided resource config parameter fence_mode {fm} '
            'is invalid. Valid values are {v}.'.format(
                fm=fence_mode, v=FENCE_MODE))

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
    """
    Perform undeploy operation on a vApp.

    :param vapp_ext:
    :param vapp_id:
    :param vapp_client:
    :param vapp_vdc:
    :param vapp_config:
    :param vapp_class:
    :param __:  CTX
    :param ___: Unused kwargs.
    :return:
    """

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
def power_off_vapp(vapp_ext,
                   vapp_id,
                   vapp_client,
                   vapp_vdc,
                   vapp_config,
                   vapp_class,
                   __,
                   **___):
    """
    Execute power off on the vApp before deletion.
    :param vapp_ext:
    :param vapp_id:
    :param vapp_client:
    :param vapp_vdc:
    :param vapp_config:
    :param vapp_class:
    :param __: CTX
    :param ___: Unused kwargs
    :return:
    """

    vapp = vapp_class(
        vapp_id,
        vapp_client,
        vapp_vdc,
        kwargs=vapp_config
    )
    if not vapp_ext:
        try:
            last_task = vapp.power_off()
            return vapp, last_task
        except (OperationNotSupportedException, BadRequestException) as e:
            ctx.logger.error('Attempted to power off the vapp, '
                             'but failed: {e}'.format(e=e))
            if no_powered_on_vms(e):
                vapp.shutdown()
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
    """
    Delete a vApp.

    :param vapp_ext:
    :param vapp_id:
    :param vapp_client:
    :param vapp_vdc:
    :param vapp_config:
    :param vapp_class:
    :param __: uUnused ctx.
    :param ___: unused kwargs
    :return:
    """

    vapp = vapp_class(
        vapp_id,
        vapp_client,
        vapp_vdc,
        kwargs=vapp_config
    )
    if not vapp_ext:
        try:
            last_task = vapp.delete()
            return vapp, last_task
        except OperationNotSupportedException as e:
            ctx.logger.error('Attempted to deleted the vapp, '
                             'but failed: {e}'.format(e=e))
    return vapp, None


@resource_operation
def create_vm(vm_external,
              vm_id,
              vm_client,
              vm_vdc,
              vm_config,
              vm_class,
              vm_ctx,
              **_):
    """
    Instiatiate a vApp and create a virtual machine.

    :param vm_external:
    :param vm_id:
    :param vm_client:
    :param vm_vdc:
    :param vm_config:
    :param vm_class:
    :param vm_ctx:
    :param _: Unused kwargs
    :return:
    """

    vapp_name = find_resource_id_from_relationship_by_type(
        vm_ctx.instance, REL_VM_VAPP)  # or vapp_id
    network = find_rel_by_type(
        vm_ctx.instance, REL_VM_NETWORK)

    if network:
        vm_config['network'] = vm_config.get(
            'network',
            network.target.instance.runtime_properties.get('resource_id'))

    vm_name = vm_config.get('vm_name')
    if vm_name != vm_id:
        ctx.logger.warn(
            'The parameter vm_name {v} in resource_config does not match '
            'the resource ID provided {i}. '
            'Using resource_id instead.'.format(v=vm_name, i=vm_id))
        vm_config['vm_name'] = vm_id

    fence_mode = vm_config.get('fence_mode')
    if fence_mode not in FENCE_MODE:
        raise NonRecoverableError(
            'The provided resource config parameter fence_mode {fm} '
            'is invalid. Valid values are {v}.'.format(
                fm=fence_mode, v=FENCE_MODE))

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

    # We want to make sure that the network has successfully provisioned.
    # Otherwise VM provisioning will fail.
    if network:
        network_type = get_network_type(network.target.node.type_hierarchy)
        if not vm.check_network(vm_config['network'], network_type):
            raise OperationRetry(
                'Waiting on the network {n} to be ready'.format(
                    n=vm_config['network']))

    try:
        last_task = vm.instantiate_vapp()
    except BadRequestException as e:
        if not (vcd_already_exists(e) and not vm_external) or bad_vm_name(e):
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
                 vm_ctx,
                 **__):

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
             vm_ctx,
             **__):
    """
    Power on both existing and new VMs.
    :param vm_external:
    :param vm_id:
    :param vm_client:
    :param vm_vdc:
    :param vm_config:
    :param vm_class:
    :param vm_ctx:
    :param __:
    :return:
    """

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

    if vm_external and vm.vm.is_powered_on():
        # VM already started and there is no further operation required.
        return vm, None
    elif vm.vm.is_powered_on():
        # VM is not external, so we can allow task to be evaluated.
        try:
            last_task = \
                vm_ctx.instance.runtime_properties['tasks']['update'][-1]
        except (KeyError, IndexError):
            vm.logger.warn('The vm {name} is powered on, '
                           'but has no previous start task '
                           'and is not external.'.format(name=vm.name))
            return vm, None
        else:
            return vm, last_task

    last_task = vm.power_on()
    expose_ip_property(vm.nics)
    return vm, last_task


@resource_operation
def stop_vm(vm_external,
            vm_id,
            vm_client,
            vm_vdc,
            vm_config,
            vm_class,
            vm_ctx,
            **__):
    """

    :param vm_external:
    :param vm_id:
    :param vm_client:
    :param vm_vdc:
    :param vm_config:
    :param vm_class:
    :param vm_ctx:
    :param __:
    :return:
    """

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
    except (AttributeError,
            BadRequestException,
            MissingLinkException,
            OperationNotSupportedException) as e:

        if not vcd_unresolved_vm(e) and not cannot_power_off(e) \
                and not isinstance(e, AttributeError):
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
              vm_ctx,
              **__):
    """

    :param vm_external:
    :param vm_id:
    :param vm_client:
    :param vm_vdc:
    :param vm_config:
    :param vm_class:
    :param vm_ctx:
    :param __: Unused kwargs
    :return:
    """

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
    except (MissingLinkException,
            OperationNotSupportedException) as e:
        if isinstance(e, MissingLinkException) or \
                (not vcd_unresolved_vm(e) and not cannot_power_off(e)):
            raise
        last_task = None

    if vm_ctx.instance.runtime_properties.get('__VM_CREATE_VAPP'):
        vm.delete()
        last_task = vm.vapp_object.delete()

    return vm, last_task


@resource_operation
def configure_nic(_,
                  __,
                  ___,
                  ____,
                  nic_config,
                  _____,
                  nic_ctx,
                  **______):
    """

    :param _: Unused external
    :param __: Unused ID
    :param ___: Unused client
    :param ____: unused vdc
    :param nic_config:
    :param _____: unused nic class (BsClass)
    :param nic_ctx:
    :param ______: Unused kwargs
    :return:
    """

    nic_network = find_resource_id_from_relationship_by_type(
        nic_ctx.instance, REL_NIC_NETWORK)
    if nic_network:
        nic_ctx.instance.runtime_properties['network'] = nic_network
    elif not nic_config['network_name']:
        raise NonRecoverableError(
            'No relationship of type {t} was provided and network_name is '
            'not in the resource config.'.format(t=REL_NIC_NETWORK))
    return None, None


@resource_operation
def add_network(_,
                __,
                ___,
                ____,
                nic_config,
                _____,
                nic_ctx,
                ______,
                vm_id,
                vm_client,
                vm_vdc,
                vm_config,
                vm_class,
                vm_ctx,
                **_______):

    """Add a network to a VM.

    :param _:  Unused external
    :param __: Unused ID
    :param ___: Unused client
    :param ____: Unused vdc
    :param nic_config:
    :param _____: Unused NIC class (BsClass)
    :param nic_ctx:
    :param ______: Unused kwargs
    :param vm_id:
    :param vm_client:
    :param vm_vdc:
    :param vm_config:
    :param vm_class:
    :param vm_ctx:
    :param _______: Unused kwargs
    :return:
    """

    vapp_name = find_resource_id_from_relationship_by_type(
        vm_ctx.instance, REL_VM_VAPP)
    nic_network = find_resource_id_from_relationship_by_type(
        nic_ctx.instance, REL_NIC_NETWORK)
    vapp_node = find_rel_by_type(vm_ctx.instance, REL_VM_VAPP)
    fence_mode = vapp_node.target.node.properties['resource_config'].get(
        'fence_mode')

    if nic_network:
        nic_config['network_name'] = nic_network

    vm = vm_class(
        vm_id,
        vapp_name,
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    )

    if nic_network not in vm.vapp_networks:
        try:
            last_task = vm.add_vapp_network(
                orgvdc_network_name=nic_config['network_name'],
                fence_mode=fence_mode)
            return vm, last_task
        except InvalidStateException as e:
            raise OperationRetry(
                'Failed to add network {n} to vm {vm} for {e}.'.format(
                    n=nic_config['network_name'], vm=vm.name, e=e))

    return vm, None


@resource_operation
def add_nic(_,
            __,
            ___,
            ____,
            nic_config,
            _____,
            nic_ctx,
            ______,
            vm_id,
            vm_client,
            vm_vdc,
            vm_config,
            vm_class,
            vm_ctx,
            **_______):
    """
    Add Nic to VM.
    :param _: Unused external nic
    :param __: Unused nic ID
    :param ___: Unused Nic client
    :param ____: Unused nic VDC
    :param nic_config:
    :param _____: Unused nic class
    :param nic_ctx:
    :param ______: Unused nic kwargs
    :param vm_id:
    :param vm_client:
    :param vm_vdc:
    :param vm_config:
    :param vm_class:
    :param vm_ctx:
    :param _______: Unused VM kwargs
    :return:
    """

    vapp_name = find_resource_id_from_relationship_by_type(
        vm_ctx.instance, REL_VM_VAPP)
    nic_network = find_resource_id_from_relationship_by_type(
        nic_ctx.instance, REL_NIC_NETWORK)

    if nic_network:
        nic_config['network_name'] = nic_network

    vm = vm_class(
        vm_id,
        vapp_name,
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    )
    last_task = None
    if not vm.get_nic_from_config(nic_config):
        last_task = vm.add_nic(**nic_config)
    nic_ctx.instance.runtime_properties['ip_address'] = None
    nic_ctx.instance.runtime_properties['mac_address'] = None
    for nic in vm.nics:
        _nic_network = nic.get('network')
        if _nic_network == nic_network:
            nic_ctx.instance.runtime_properties['ip_address'] = \
                nic.get('ip_address')
            nic_ctx.instance.runtime_properties['mac_address'] = \
                nic.get('mac_address')
            break
    return vm, last_task


@resource_operation
def delete_nic(_,
               __,
               ___,
               ____,
               nic_config,
               _____,
               nic_ctx,
               ______,
               vm_id,
               vm_client,
               vm_vdc,
               vm_config,
               vm_class,
               vm_ctx,
               **_______):
    """
    Delete NIC and remove network from vapp.
    :param _: Unused external nic
    :param __: Unused nic ID
    :param ___: Unused Nic client
    :param ____: Unused nic VDC
    :param nic_config:
    :param _____: Unused nic class
    :param nic_ctx:
    :param ______: Unused nic kwargs
    :param vm_id:
    :param vm_client:
    :param vm_vdc:
    :param vm_config:
    :param vm_class:
    :param vm_ctx:
    :param _______: Unused VM kwargs
    :return:
    """

    vapp_name = find_resource_id_from_relationship_by_type(
        vm_ctx.instance, REL_VM_VAPP)
    nic_network = find_resource_id_from_relationship_by_type(
        nic_ctx.instance, REL_NIC_NETWORK)
    if nic_network:
        nic_config['network_name'] = nic_network
    vm = vm_class(
        vm_id,
        vapp_name,
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    )
    nic = vm.get_nic_from_config(nic_config)

    if nic:
        # I wish we had another operation in order to split these. :(
        delete_nic_task = vm.delete_nic(nic['index'])
        result = vm.client.get_task_monitor().wait_for_success(
            delete_nic_task, 10)
        if result.get('status') != TaskStatus.SUCCESS.value:
            raise OperationRetry(
                'Waiting for NIC delete to complete '
                'before removing network from the vApp.')

    if nic_config['network_name'] in vm.vapp_networks:
        last_task = vm.remove_vapp_network(nic_config['network_name'])
        return vm, last_task

    ctx.logger.warn(
        'The NIC {config} was not found, '
        'so we cannot remove it from the VM.'.format(config=nic_config))

    return vm, None
