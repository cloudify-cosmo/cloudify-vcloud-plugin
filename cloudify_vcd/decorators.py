
from pyvcloud.vcd.exceptions import (
    AccessForbiddenException,
    EntityNotFoundException,
    MissingLinkException,
    BadRequestException,
    NotFoundException)

from functools import wraps

from cloudify.decorators import operation
from cloudify.exceptions import (
    OperationRetry,
    NonRecoverableError)

from .constants import NO_RESOURCE_OK
from .utils import (
    expose_props,
    get_last_task,
    retry_or_raise,
    invalid_resource,
    get_resource_data,
    check_if_task_successful)
from vcd_plugin_sdk.exceptions import VCloudSDKException


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
                    MissingLinkException,
                    BadRequestException,
                    VCloudSDKException,
                    NotFoundException) as e:
                ctx.logger.error(
                    'Failed to execute func {func} '
                    'with args {args} '
                    'kwargs {kwargs} '
                    'Error: {e}'.format(func=func,
                                        args=args,
                                        kwargs=kwargs,
                                        e=str(e)))
                retry_or_raise(e, resource_data, operation_name)
            else:
                last_task = get_last_task(result)

        if not resource:
            args[0] = True  # Tell the function to expect external resource.
            try:
                resource, _ = func(*args, **kwargs)
            except (TypeError, NotFoundException, EntityNotFoundException):
                ctx.logger.error('Attempted to perform {op} '
                                 'operation on {r}, '
                                 'but the resource was not '
                                 'found.'.format(
                                     op=operation_name,
                                     r=resource_data.primary_id))
                if operation_name not in NO_RESOURCE_OK:
                    raise NonRecoverableError(
                        'The expected resource {r} does not exist.'.format(
                            r=resource_data.primary_id))
            except AccessForbiddenException as e:
                if not invalid_resource(e):
                    raise OperationRetry(e)

        if not check_if_task_successful(resource, last_task):
            resource_data.primary_ctx.instance.runtime_properties[
                '__RETRY_BAD_REQUEST'] = True
            raise OperationRetry('Pending for operation completion.')
        expose_props(operation_name,
                     resource,
                     _ctx=resource_data.primary_ctx)

    return operation(func=wrapper, resumable=True)
