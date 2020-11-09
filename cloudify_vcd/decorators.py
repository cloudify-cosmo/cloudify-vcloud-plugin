
from pyvcloud.vcd.exceptions import (
    UnauthorizedException,
    BadRequestException)

from functools import wraps

from cloudify.decorators import operation
from cloudify.exceptions import (
    NonRecoverableError)

from .utils import (
    expose_props,
    get_last_task,
    get_resource_data
)


def resource_operation(func):
    @wraps(func)
    def wrapper(*_, **kwargs):
        resource = None
        ctx = kwargs.pop('ctx', None)
        resource_data = get_resource_data(ctx)
        args = resource_data.primary
        if resource_data.secondary:
            args.extend(resource_data.secondary)
        last_task = get_last_task(
            resource_data.primary_ctx.instance.runtime_properties.get(
                '__last_task'))

        if not ctx.operation.retry_number:
            try:
                resource, result = func(*args, **kwargs)
            except BadRequestException as e:
                # TODO: FIx this: 2020-11-09 17:02:42.978  CFY <test-33>
                # 'install' workflow execution failed: Task failed
                # 'cloudify_vcd.network_tasks.create_network' -> Status code:
                #  400/BAD_REQUEST, [ 8dd248ef-72af-4cc2-b232-53ece0165415 ]
                # Edge gateway (
                # com.vmware.vcloud.entity.gateway:6e2b7a08-a942-4357-96df
                # -08996e2d2c05) is busy, cannot proceed with the operation.
                # (request id: 8dd248ef-72af-4cc2-b232-53ece0165415)
                # TODO: This will be a bug on day 2.
                if not last_task:
                    raise NonRecoverableError(str(e))
            else:
                last_task = get_last_task(result)

        if not resource:
            args[0] = True  # Tell the function to expect external resource.
            resource, _ = func(*args, **kwargs)

        if last_task:
            resource.task_successful(last_task)
        expose_props(ctx.operation.name.split('.')[-1], resource)

    return operation(func=wrapper, resumable=True)
