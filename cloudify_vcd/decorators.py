
from pyvcloud.vcd.exceptions import (
    AccessForbiddenException,
    EntityNotFoundException,
    UnauthorizedException,
    BadRequestException,
    NotFoundException,
    VcdTaskException)

from functools import wraps

from cloudify.decorators import operation
from cloudify.exceptions import (
    OperationRetry,
    NonRecoverableError)

from .constants import NO_RESOURCE_OK
from .utils import (
    expose_props,
    get_last_task,
    get_resource_data,
    vcd_busy_exception,
    vcd_unclear_exception,
    check_if_task_successful)


def resource_operation(func):
    @wraps(func)
    def wrapper(*_, **kwargs):
        resource = None
        ctx = kwargs.pop('ctx', None)
        operation_name = ctx.operation.name.split('.')[-1]
        resource_data = get_resource_data(ctx)
        args = resource_data.primary
        if resource_data.secondary:
            args.extend(resource_data.secondary)
        last_task = get_last_task(
            resource_data.primary_ctx.instance.runtime_properties.get(
                '__last_task'))

        if not resource_data.primary_external:
            try:
                ctx.logger.debug('Executing func {func} '
                                 'with args {args} '
                                 'kwargs {kwargs}'.format(
                                     func=func, args=args, kwargs=kwargs))
                resource, result = func(*args, **kwargs)
                ctx.logger.debug('Executed func {func} '
                                 'result {result}'.format(
                                     func=func, result=result))
            except (AccessForbiddenException,
                    EntityNotFoundException,
                    BadRequestException,
                    NotFoundException) as e:
                ctx.logger.error(
                    'Failed to execute func {func} '
                    'with args {args} '
                    'kwargs {kwargs} '
                    'Error: {e}'.format(func=func,
                                        args=args,
                                        kwargs=kwargs,
                                        e=str(e)))
                if isinstance(e, (TypeError,
                                  NotFoundException,
                                  EntityNotFoundException)):
                    if operation_name not in NO_RESOURCE_OK:
                        raise NonRecoverableError(
                            'The expected resource {r} does not exist.'.format(
                                r=resource_data.primary_id))
                    ctx.logger.error('Attempted to perform {op} '
                                     'operation on {r}, '
                                     'but the resource was not '
                                     'found.'.format(
                                         op=operation_name,
                                         r=resource_data.primary_id))
                elif vcd_busy_exception(e) or vcd_unclear_exception(e):
                    resource_data.primary_ctx.instance.runtime_properties[
                        '__RETRY_BAD_REQUEST'] = True
                    resource_data.primary_ctx.instance.update()
                    raise OperationRetry(str(e))
            else:
                last_task = get_last_task(result)

        if not resource:
            args[0] = True  # Tell the function to expect external resource.
            try:
                resource, _ = func(*args, **kwargs)
            except (TypeError, NotFoundException, EntityNotFoundException):
                if operation_name not in NO_RESOURCE_OK:
                    raise NonRecoverableError(
                        'The expected resource {r} does not exist.'.format(
                            r=resource_data.primary_id))
                ctx.logger.error('Attempted to perform {op} '
                                 'operation on {r},'
                                 'but the resource was not '
                                 'found.'.format(
                                     op=operation_name,
                                     r=resource_data.primary_id))

        if not check_if_task_successful(resource, last_task):
            resource_data.primary_ctx.instance.runtime_properties[
                '__RETRY_BAD_REQUEST'] = True
            raise OperationRetry('Pending for operation completion.')
        expose_props(operation_name,
                     resource,
                     _ctx=resource_data.primary_ctx)

    return operation(func=wrapper, resumable=True)
