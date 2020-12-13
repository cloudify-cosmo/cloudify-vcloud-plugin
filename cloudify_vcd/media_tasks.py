from .decorators import resource_operation

from vcd_plugin_sdk.resources.disk import VCloudISO


@resource_operation
def create_media(external_media,
                 media_id,
                 media_client,
                 media_vdc,
                 media_config,
                 media_class,
                 media_ctx,
                 **___):
    iso = VCloudISO(media_ctx.node.properties['iso'])
    media_config['file_name'] = iso.file
    media = media_class(media_id,
                        media_client,
                        media_vdc,
                        media_config,
                        media_ctx.instance.runtime_properties.get('tasks'))

    if external_media:
        return media, None

    VCloudISO(media_ctx.node.properties['iso'])
    media.upload()
    return media, None


@resource_operation
def delete_media(external_media,
                 media_id,
                 media_client,
                 media_vdc,
                 media_config,
                 media_class,
                 media_ctx,
                 **___):
    media = media_class(media_id,
                        media_client,
                        media_vdc,
                        media_config,
                        media_ctx.instance.runtime_properties.get('tasks'))
    if external_media:
        return media, None
    last_task = media.delete()
    return media, last_task


@resource_operation
def attach_media(_,
                 media_id,
                 media_client,
                 media_vdc,
                 media_config,
                 media_class,
                 media_ctx,
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
    media = media_class(media_id,
                        media_client,
                        media_vdc,
                        media_config,
                        media_ctx.instance.runtime_properties.get('tasks'))
    last_task = vm.attach_media(media.href)
    return media, last_task


@resource_operation
def detach_media(_,
                 media_id,
                 media_client,
                 media_vdc,
                 media_config,
                 media_class,
                 media_ctx,
                 __,
                 vm_id,
                 vm_client,
                 vm_vdc,
                 vm_config,
                 vm_class,
                 vm_ctx,
                 **___):
    vapp_name = vm_ctx.instance.runtime_properties.get('data', {}).get('vapp')
    if not vapp_name:
        return
    vm = vm_class(
        vm_id,
        vapp_name,
        vm_client,
        vdc_name=vm_vdc,
        kwargs={},
        vapp_kwargs=vm_config
    )
    media = media_class(media_id,
                        media_client,
                        media_vdc,
                        media_config,
                        media_ctx.instance.runtime_properties.get('tasks'))
    last_task = vm.eject_media(media.id)
    return media, last_task
