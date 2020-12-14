from cloudify import ctx

from .decorators import resource_operation


@resource_operation
def create_disk(external_disk,
                disk_id,
                disk_client,
                disk_vdc,
                disk_config,
                disk_class,
                disk_ctx,
                **___):
    disk = disk_class(disk_id,
                      disk_client,
                      disk_vdc,
                      disk_config,
                      disk_ctx.instance.runtime_properties.get('tasks'))
    if external_disk:
        return disk, None
    last_task = disk.create()
    return disk, last_task


@resource_operation
def delete_disk(external_disk,
                disk_id,
                disk_client,
                disk_vdc,
                disk_config,
                disk_class,
                disk_ctx,
                **___):
    disk = disk_class(disk_id,
                      disk_client,
                      disk_vdc,
                      disk_config,
                      disk_ctx.instance.runtime_properties.get('tasks'))
    if external_disk:
        return disk, None
    last_task = disk.delete()
    return disk, last_task


@resource_operation
def attach_disk(_,
                disk_id,
                disk_client,
                disk_vdc,
                disk_config,
                disk_class,
                disk_ctx,
                __,
                vm_id,
                vm_client,
                vm_vdc,
                vm_config,
                vm_class,
                vm_ctx,
                **___):
    vm = vm_class(
        vm_id,
        vm_ctx.instance.runtime_properties['data']['vapp'],
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    )
    disk = disk_class(disk_id,
                      disk_client,
                      disk_vdc,
                      disk_config,
                      disk_ctx.instance.runtime_properties.get('tasks'))
    last_task = vm.attach_disk_to_vm(disk.href)
    return disk, last_task


@resource_operation
def detach_disk(_,
                disk_id,
                disk_client,
                disk_vdc,
                disk_config,
                disk_class,
                disk_ctx,
                __,
                vm_id,
                vm_client,
                vm_vdc,
                vm_config,
                vm_class,
                vm_ctx,
                **___):
    vapp_name = vm_ctx.instance.runtime_properties.get('data', {}).get('vapp')

    vm = vm_class(
        vm_id,
        vapp_name,
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    )
    disk = disk_class(disk_id,
                      disk_client,
                      disk_vdc,
                      disk_config,
                      disk_ctx.instance.runtime_properties.get('tasks'))
    if not vapp_name:
        ctx.logger.warn('No vapp was found to detach disk {n}.'.format(
            n=disk_id))
        last_task = None
    else:
        last_task = vm.detach_disk_from_vm(disk.href)
    return disk, last_task
