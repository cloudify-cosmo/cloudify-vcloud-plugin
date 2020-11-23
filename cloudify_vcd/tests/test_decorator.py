import mock
import pytest

from pyvcloud.vcd.client import E
from cloudify.exceptions import (OperationRetry, NonRecoverableError)
from pyvcloud.vcd.exceptions import (
    VcdTaskException,
    BadRequestException,
    EntityNotFoundException,
    AccessForbiddenException)

from ..decorators import resource_operation
from .test_utils import (
    get_mock_relationship_context,
    get_mock_node_instance_context)


@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_external_resource_exists(*_, **__):
    """
    Test the happy scenario when an existing resource is found.
    :param _:
    :param __:
    :return:
    """
    operation = {'name': 'create', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'resource_config': {'foo': 'bar'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _task = E.Task(
        status='foo',
        serviceNamespace='bar',
        type='baz',
        operation='taco',
        operationName='bell',
        name='task')

    @resource_operation
    def test_func(ext, name, client, vdc, config, obj, __ctx):
        return obj(name, 'bar', client, vdc, {}, config), _task
    test_func(ctx=_ctx)
    assert '__created' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_external_resource_not_exists(*_, **__):
    """
    Test unhappy scenario when existing resource is not found.
    :param _:
    :param __:
    :return:
    """
    operation = {'name': 'foo', 'retry_number': 1}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'resource_config': {'foo': 'bar'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
        operation=operation
    )
    _task = E.Task(
        status='foo',
        serviceNamespace='bar',
        type='baz',
        operation='taco',
        operationName='bell',
        name='task')

    @resource_operation
    def test_func(*__, **____):
        raise EntityNotFoundException()

    with pytest.raises(NonRecoverableError) as e_info:
        test_func(ctx=_ctx)
        assert 'resource was not found' in e_info


@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_external_resource_not_exists_create_op(*_, **__):
    """
    Test unhappy scenario when existing resource is not found.
    :param _:
    :param __:
    :return:
    """
    operation = {'name': 'create', 'retry_number': 1}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': True,
            'resource_id': 'foo',
            'resource_config': {'foo': 'bar'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
        operation=operation
    )
    _task = E.Task(
        status='foo',
        serviceNamespace='bar',
        type='baz',
        operation='taco',
        operationName='bell',
        name='task')

    @resource_operation
    def test_func(*__, **____):
        raise EntityNotFoundException()

    with pytest.raises(NonRecoverableError) as e_info:
        test_func(ctx=_ctx)
        assert 'operation on foo' in e_info


@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_implicit_external_resource_bad_request(*_, **__):
    """
    Test unhappy scenario when an implicit external resource
    (new resource that requires retry for task completion)
    hits a retryable error.
    :param _:
    :param __:
    :return:
    """
    operation = {'name': 'foo', 'retry_number': 1}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'foo': 'bar'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
        operation=operation
    )
    _ctx.instance.runtime_properties['__RETRY_BAD_REQUEST'] = True
    _task = E.Task(
        status='foo',
        serviceNamespace='bar',
        type='baz',
        operation='taco',
        operationName='bell',
        name='task')

    @resource_operation
    def test_func(*__, **____):
        raise BadRequestException(
            400,
            'foo',
            {
                'message': 'cannot be deleted, because it is in use',
                'minorCode': 400
            }
        )

    with pytest.raises(OperationRetry) as e_info:
        test_func(ctx=_ctx)
        assert 'cannot be deleted, because it is in use' in e_info


@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_new_resource(*_, **__):
    """
    Check the happy scenario when a new resource is created.
    :param _:
    :param __:
    :return:
    """
    operation = {'name': 'create', 'retry_number': 0}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'foo': 'bar'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
            operation=operation)
    _task = E.Task(
        status='foo',
        serviceNamespace='bar',
        type='baz',
        operation='taco',
        operationName='bell',
        name='task')

    @resource_operation
    def test_func(ext, name, client, vdc, config, obj, __ctx):
        return obj(name, 'bar', client, vdc, {}, config), _task
    test_func(ctx=_ctx)
    assert '__created' in _ctx.instance.runtime_properties


@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_new_resource_access_forbidden(*_, **__):
    """
    Check the unhappy scenario when we get access forbidden when trying
    to create a new resource.
    :param _:
    :param __:
    :return:
    """
    operation = {'name': 'foo', 'retry_number': 1}
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'foo': 'bar'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
        operation=operation
    )
    _task = E.Task(
        status='foo',
        serviceNamespace='bar',
        type='baz',
        operation='taco',
        operationName='bell',
        name='task')

    @resource_operation
    def test_func(*__, **____):
        raise AccessForbiddenException()

    with pytest.raises(NonRecoverableError) as e_info:
        test_func(ctx=_ctx)
        assert 'resource was not found' in e_info


@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_new_resource_bad_request_handled(*_, **__):
    """
    Check the unhappy scenario when we try to create a new resource
    and a bad request is handled.
    :param _:
    :param __:
    :return:
    """
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'foo': 'bar'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
    )
    _task = E.Task(
        status='foo',
        serviceNamespace='bar',
        type='baz',
        operation='taco',
        operationName='bell',
        name='task')

    @resource_operation
    def test_func(*__, **____):
        raise BadRequestException(
            400,
            'foo',
            {
                'message': 'is busy, cannot proceed with the operation',
                'minorCode': 400
            }
        )

    with pytest.raises(OperationRetry) as e_info:
        test_func(ctx=_ctx)
        assert 'is busy, cannot proceed with the operation' in e_info


@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_new_resource_not_found(*_, **__):
    """
    Test the unhappy scenario when we create a new resource, which is
    subsequently not found. Or if we try to hit a dependency which
    fails.
    :param _:
    :param __:
    :return:
    """
    _ctx = get_mock_node_instance_context(properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'foo': 'bar'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}},
    )
    _task = E.Task(
        status='foo',
        serviceNamespace='bar',
        type='baz',
        operation='taco',
        operationName='bell',
        name='task')

    @resource_operation
    def test_func(*__, **____):
        raise EntityNotFoundException(
            400,
            'foo',
            {
                'message': 'unhandled error',
                'minorCode': 400
            }
        )

    with pytest.raises(NonRecoverableError) as e_info:
        test_func(ctx=_ctx)
        assert 'unhandled' in e_info


@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
@mock.patch('cloudify_vcd.decorators.check_if_task_successful',
            return_value=True)
def test_new_relationship_resource(*_, **__):
    """
    Check the happy scenario when a new relationship resource is created.
    :param _:
    :param __:
    :return:
    """
    _ctx = get_mock_relationship_context(related={'is_target': True})
    _task = E.Task(
        status='foo',
        serviceNamespace='bar',
        type='baz',
        operation='taco',
        operationName='bell',
        name='task')

    @resource_operation
    def test_func(ext, name, client, vdc, config, obj, __ctx,
                  ext2, name2, client2, vdc2, config2, obj2, __ctx2):
        return obj(name, 'bar', client, vdc, {}, config), _task
    test_func(ctx=_ctx)


@mock.patch('cloudify_vcd.constants.VCloudVM.exposed_data')
@mock.patch('cloudify_vcd.utils.VCloudConnect', logger='foo')
def test_new_relationship_resource_not_found(*_, **__):
    """
    Test unhappy scenario when new relationship resource is not found.
    :param _:
    :param __:
    :return:
    """
    operation = {'name': 'create', 'retry_number': 1}
    _ctx = get_mock_relationship_context(operation=operation)
    _task = E.Task(
        status='foo',
        serviceNamespace='bar',
        type='baz',
        operation='taco',
        operationName='bell',
        name='task')

    @resource_operation
    def test_func(*__, **____):
        raise EntityNotFoundException()

    with pytest.raises(NonRecoverableError) as e_info:
        test_func(ctx=_ctx)
        assert 'operation on foo' in e_info
