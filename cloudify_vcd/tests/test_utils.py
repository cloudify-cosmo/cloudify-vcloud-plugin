import mock
import pytest

from lxml import objectify
from pyvcloud.vcd.client import E
from cloudify.state import current_ctx
from cloudify.manager import DirtyTrackingDict
from vcd_plugin_sdk.connection import VCloudConnect
from cloudify.mocks import MockCloudifyContext
from vcd_plugin_sdk.resources.vapp import VCloudVM, VCloudvApp
from cloudify.exceptions import (OperationRetry, NonRecoverableError)
from pyvcloud.vcd.exceptions import (
    VcdTaskException,
    BadRequestException,
    EntityNotFoundException)

from ..utils import (
    get_ctxs,
    ResourceData,
    expose_props,
    get_last_task,
    retry_or_raise,
    is_relationship,
    get_resource_id,
    is_node_instance,
    find_rel_by_type,
    get_client_config,
    get_resource_data,
    cleanup_objectify,
    find_rels_by_type,
    get_resource_class,
    get_resource_config,
    is_external_resource,
    use_external_resource,
    check_if_task_successful,
    update_runtime_properties,
    cleanup_runtime_properties,
    find_resource_id_from_relationship_by_type)


class SpecialMockCloudifyContext(MockCloudifyContext):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        setattr(self, 'properties', kwargs.get('properties'))
        self._plugin = mock.MagicMock(properties={})

    @property
    def plugin(self):
        return self._plugin


def get_mock_node_instance_context(**kwargs):
    kwargs['node_id'] = kwargs.get('node_id', 'foo')
    kwargs['node_name'] = kwargs.get('node_id', 'foo')
    kwargs['properties'] = kwargs.get(
        'properties',
        {
            'use_external_resource': False,
            'resource_id': 'foo',
            'resource_config': {'foo': 'bar'},
            'client_config': {'foo': 'bar', 'vdc': 'vdc'}
        }
    )
    kwargs['runtime_properties'] = DirtyTrackingDict(
        kwargs.get('runtime_properties', {}))
    kwargs['operation'] = kwargs.get(
        'operation',
        {'name': 'foo', 'retry_number': 0})
    _ctx = SpecialMockCloudifyContext(**kwargs)
    _ctx.node.type_hierarchy = ['cloudify.nodes.Root',
                                'cloudify.nodes.Compute',
                                'cloudify.nodes.vcloud.VM']
    current_ctx.set(_ctx)
    return _ctx


def get_mock_relationship_context(**kwargs):
    source_node = mock.Mock(
        id='foo',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.Compute',
            'cloudify.nodes.vcloud.VM'
        ],
        properties={
            'use_external_resource': False,
            'resource_id': 'foo',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    source_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'foo'})
    )
    target_node = mock.Mock(
        id='bar',
        type_hierarchy=[
            'cloudify.nodes.Root',
            'cloudify.nodes.vcloud.VApp'
        ],
        properties={
            'use_external_resource': True,
            'resource_id': 'bar',
            'client_config': {
                'foo': 'bar',
                'vdc': 'vdc'
            }
        },
    )
    target_instance = mock.Mock(
        runtime_properties=DirtyTrackingDict({'resource_id': 'bar'})
    )
    source = mock.Mock(node=source_node, instance=source_instance)
    target = mock.Mock(node=target_node, instance=target_instance)
    kwargs['source'] = kwargs.get('source', source)
    kwargs['target'] = kwargs.get('target', target)
    kwargs['related'] = kwargs.get('related', {'is_target': False})
    kwargs['operation'] = kwargs.get(
        'operation',
        {'name': 'foo', 'retry_number': 0})
    _ctx = SpecialMockCloudifyContext(**kwargs)
    _ctx._context = {'related': kwargs.get('related', {'is_target': False})}
    current_ctx.set(_ctx)
    return _ctx


def test_resource_data_object():
    data = {
        'context': 'context',
        'external': 'external',
        'resource_id': 'resource_id',
        'client_config': 'client_config',
        'vdc': 'vdc',
        'resource_config': 'resource_config',
        'resource_class': mock.Mock
    }
    primary_data = ['external',
                    'resource_id',
                    'client_config',
                    'vdc',
                    'resource_config',
                    mock.Mock,
                    'context']
    resource_data = ResourceData(*list(data.values()))
    assert resource_data.primary == primary_data
    resource_data.add(*list(data.values()))
    assert resource_data.secondary == primary_data
    assert resource_data.primary_id == 'resource_id'
    assert resource_data.primary_class == mock.Mock
    assert resource_data.primary_client == 'client_config'
    assert resource_data.primary_ctx == 'context'
    assert resource_data.primary_external == 'external'
    assert resource_data.primary_vdc == 'vdc'
    assert isinstance(resource_data.primary_resource, mock.Mock)


def test_is_relationship():
    assert not is_relationship(get_mock_node_instance_context())
    assert is_relationship(get_mock_relationship_context())


def test_is_node_instance():
    assert not is_node_instance(get_mock_relationship_context())
    assert is_node_instance(get_mock_node_instance_context())


def test_get_resource_config():
    props = {
        'properties': {'resource_config': 'foo'},
        'runtime_properties': {'resource_config': 'foo'}
    }
    ctx = get_mock_node_instance_context(**props)
    assert get_resource_config(ctx.node.properties,
                               ctx.instance.runtime_properties) == 'foo'


def test_is_external_resource():
    props = {
        'properties': {'use_external_resource': True}
    }
    ctx = get_mock_node_instance_context(**props)
    assert is_external_resource(ctx.node.properties,
                                ctx.instance.runtime_properties)

    operation = {'name': 'foo', 'retry_number': 1}
    props = {
        'properties': {'use_external_resource': False},
        'runtime_properties': {'__RETRY_BAD_REQUEST': False},
        'operation': operation
    }
    ctx = get_mock_node_instance_context(**props)
    assert is_external_resource(ctx.node.properties,
                                ctx.instance.runtime_properties)

    ctx = get_mock_node_instance_context()
    assert not is_external_resource(ctx.node.properties,
                                    ctx.instance.runtime_properties)

    operation = {'name': 'foo', 'retry_number': 1}
    props = {
        'properties': {'use_external_resource': False},
        'runtime_properties': {'__RETRY_BAD_REQUEST': True},
        'operation': operation
    }
    ctx = get_mock_node_instance_context(**props)
    assert not is_external_resource(ctx.node.properties,
                                    ctx.instance.runtime_properties)


def test_get_resource_id():
    ctx = get_mock_node_instance_context()
    assert get_resource_id(ctx.node.properties,
                           ctx.instance.runtime_properties) == 'foo'
    assert get_resource_id(ctx.node.properties,
                           ctx.instance.runtime_properties,
                           ctx.instance.id) == 'foo'


def test_get_client_config():
    ctx = get_mock_node_instance_context()
    client, _ = get_client_config(ctx.node.properties)
    assert isinstance(client, VCloudConnect)


def test_get_ctxs():
    ni_ctx = get_mock_node_instance_context()
    a, b = get_ctxs(ni_ctx)
    assert a, not b

    rel_ctx = get_mock_relationship_context(related={'is_target': True})
    a, b = get_ctxs(rel_ctx)
    assert a, b
    assert a.node.id == 'foo'
    assert b.node.id == 'bar'

    rel_ctx = get_mock_relationship_context()
    a, b = get_ctxs(rel_ctx)
    assert a, b
    assert a.node.id == 'bar'
    assert b.node.id == 'foo'


def test_get_resource_class():
    type_hierarchy = ['cloudify.nodes.Root',
                      'cloudify.nodes.Compute',
                      'cloudify.nodes.vcloud.VM',
                      'extended_vm_type']
    assert get_resource_class(type_hierarchy) == [VCloudVM, VCloudvApp]
    with pytest.raises(NonRecoverableError):
        get_resource_class([])


def test_get_resource_data():
    ni_ctx = get_mock_node_instance_context()
    rel_ctx = get_mock_relationship_context()

    result = get_resource_data(ni_ctx)
    assert isinstance(result.primary, list)
    assert not result.primary_external
    assert result.primary_id == 'foo'
    assert isinstance(result.primary_client, VCloudConnect)
    assert result.primary_class == VCloudVM
    assert result.primary_vdc == 'vdc'

    result = get_resource_data(rel_ctx)
    assert isinstance(result.primary, list)
    assert result.primary_external
    assert result.primary_id == 'bar'
    assert isinstance(result.primary_client, VCloudConnect)
    assert result.primary_class == VCloudvApp
    assert result.primary_vdc == 'vdc'
    assert not result.secondary[0]
    assert result.secondary[1] == 'foo'


def test_update_runtime_properties():
    ctx = get_mock_node_instance_context()
    update_runtime_properties(ctx, {'taco': 'bell'})
    assert ctx.instance.runtime_properties['taco'] == 'bell'


def test_update_runtime_properties_relationship():
    ctx = get_mock_relationship_context()
    update_runtime_properties(ctx.target, {'taco': 'bell'})
    assert ctx.target.instance.runtime_properties['taco'] == 'bell'


def test_cleanup_runtime_properties():
    ctx = get_mock_node_instance_context()
    ctx.instance.runtime_properties['taco'] = 'bell'
    cleanup_runtime_properties(ctx)
    assert 'taco' not in ctx.instance.runtime_properties


def test_cleanup_runtime_properties_relationship():
    ctx = get_mock_relationship_context()
    ctx.source.instance.runtime_properties['taco'] = 'bell'
    cleanup_runtime_properties(ctx.source)
    assert 'taco' not in ctx.source.instance.runtime_properties


def test_cleanup_objectify():
    data = {
        'tuple': ('foo'),
        'dict': {
            'list': ['bar'],
            'ObjectifiedElement': objectify.fromstring(
                "<root>"
                "<StringElement>test</StringElement>"
                "<IntElement>5</IntElement>"
                "<BoolElement>true</BoolElement>"
                "</root>"
            )
        }
    }
    expected = {
        'tuple': ('foo'),
        'dict': {
            'list': ['bar'],
            'ObjectifiedElement': {
                'StringElement': 'test',
                'IntElement': 5,
                'BoolElement': True
            }
        }
    }
    assert cleanup_objectify(data) == expected


def test_find_rels_by_type():
    relationships = [
        mock.Mock(type_hierarchy=['a', 'b', 'c']),
        mock.Mock(type_hierarchy=['b', 'c', 'd']),
        mock.Mock(type_hierarchy=['c', 'd', 'e']),
        mock.Mock(type_hierarchy=['x', 'y', 'z']),
    ]
    node_instance = mock.Mock(relationships=relationships)
    assert len(find_rels_by_type(node_instance, 'c')) == 3


def test_find_rel_by_type():
    relationships = [
        mock.Mock(id=1, type_hierarchy=['a', 'b', 'c']),
        mock.Mock(id=2, type_hierarchy=['b', 'c', 'd']),
        mock.Mock(id=3, type_hierarchy=['c', 'd', 'e']),
        mock.Mock(id=4, type_hierarchy=['x', 'y', 'z']),
    ]
    node_instance = mock.Mock(relationships=relationships)
    assert not find_rel_by_type(node_instance, 'd')
    assert find_rel_by_type(node_instance, 'x').id == 4


def test_find_resource_id_from_relationship_by_type():
    relationships = [
        mock.Mock(id=1,
                  type_hierarchy=['a', 'b', 'c'],
                  target=mock.Mock(
                      instance=mock.Mock(
                          runtime_properties={'resource_id': 1}))),
        mock.Mock(id=2,
                  type_hierarchy=['b', 'c', 'd'],
                  target=mock.Mock(
                      instance=mock.Mock(
                          runtime_properties={'resource_id': 2}))),
        mock.Mock(id=3,
                  type_hierarchy=['d', 'e', 'f'],
                  target=mock.Mock(
                      instance=mock.Mock(
                          runtime_properties={'resource_id': 3}))),
        mock.Mock(id=4,
                  type_hierarchy=['x', 'y', 'z'],
                  target=mock.Mock(
                      instance=mock.Mock(
                          runtime_properties={'resource_id': 4}))),
    ]
    node_instance = mock.Mock(relationships=relationships)
    assert find_resource_id_from_relationship_by_type(node_instance, 'a') == 1


def test_use_external_resource():
    assert not use_external_resource(False, False, False, 'foo', 'bar')
    assert not use_external_resource(True, False, True, 'foo', 'bar')
    assert use_external_resource(True, True, False, 'foo', 'bar')
    with pytest.raises(NonRecoverableError):
        use_external_resource(True, False, False, 'foo', 'bar')


def test_expose_runtime_properties():
    ctx = get_mock_node_instance_context()
    resource = mock.Mock(
        name='foo',
        exposed_data={'taco': 'bell'},
        tasks={'create': [[{'id': 'bar'}, {'href': 'foo/bar'}]], 'delete': []}
    )
    expose_props('create', resource, {'goodgirl': 'turnedbad'}, ctx)
    assert 'taco' in ctx.instance.runtime_properties['data']
    assert not ctx.instance.runtime_properties['__RETRY_BAD_REQUEST']
    assert 'create', 'delete' in ctx.instance.runtime_properties['tasks']
    assert 'id', 'href' in ctx.instance.runtime_properties['tasks']['create']
    assert ctx.instance.runtime_properties['__created']

    expose_props('modify', resource, {}, ctx)
    assert 'taco' in ctx.instance.runtime_properties['data']
    assert not ctx.instance.runtime_properties['__RETRY_BAD_REQUEST']
    assert 'create', 'delete' in ctx.instance.runtime_properties['tasks']
    assert 'id', 'href' in ctx.instance.runtime_properties['tasks']['create']
    assert ctx.instance.runtime_properties['__created']

    expose_props('delete', resource, {}, ctx)
    assert 'data' not in ctx.instance.runtime_properties
    assert not ctx.instance.runtime_properties['__RETRY_BAD_REQUEST']
    assert 'create', 'delete' not in ctx.instance.runtime_properties['tasks']
    assert 'id', 'href' not in \
                 ctx.instance.runtime_properties['tasks']['create']
    assert ctx.instance.runtime_properties['__deleted']


def test_get_last_task():

    task = E.Task(
        status='foo',
        serviceNamespace='bar',
        type='baz',
        operation='taco',
        operationName='bell',
        name='task')
    result = get_last_task(task)
    assert result.get('status') == 'foo'
    assert result.get('serviceNamespace') == 'bar'
    assert result.get('type') == 'baz'
    assert result.get('operation') == 'taco'
    assert result.get('operationName') == 'bell'
    assert result.get('name') == 'task'


def test_retry_or_raise():
    resource = mock.Mock(
        primary_id='foo',
        primary_ctx=get_mock_node_instance_context()
    )
    with pytest.raises(NonRecoverableError) as e_info:
        retry_or_raise(EntityNotFoundException(), resource, 'create')
        assert 'foo' in e_info
    with pytest.raises(NonRecoverableError) as e_info:
        retry_or_raise(EntityNotFoundException(), resource, 'configure')
        assert 'foo' in e_info
    with pytest.raises(NonRecoverableError) as e_info:
        retry_or_raise(EntityNotFoundException(), resource, 'start')
        assert 'foo' in e_info
    with pytest.raises(NonRecoverableError) as e_info:
        retry_or_raise(EntityNotFoundException(), resource, 'establish')
        assert 'foo' in e_info
    retry_or_raise(EntityNotFoundException(), resource, 'unlink')
    retry_or_raise(EntityNotFoundException(), resource, 'stop')
    retry_or_raise(EntityNotFoundException(), resource, 'delete')
    with pytest.raises(OperationRetry) as e_info:
        retry_or_raise(
            BadRequestException(
                400,
                'foobar',
                {
                    'message': 'is busy, cannot proceed with the operation',
                    'minorErrorCode': 400
                }
            ),
            resource,
            'create'
        )
        assert resource.primary_ctx.instance.runtime_properties[
            '__RETRY_BAD_REQUEST']
        assert 'is busy, cannot proceed with the operation' in e_info
    del resource.primary_ctx.instance.runtime_properties['__RETRY_BAD_REQUEST']


def test_check_if_task_successful():
    task = E.Task(
        status='foo',
        serviceNamespace='bar',
        type='baz',
        operation='taco',
        operationName='bell',
        name='task')
    resource = mock.Mock()
    resource.task_successful.side_effect = VcdTaskException(
        400,
        {
            'message': 'Cannot deploy organization VDC network',
            'minorErrorCode': 400
        })
    with pytest.raises(NonRecoverableError) as e_info:
        check_if_task_successful(resource, task)
        assert 'Cannot deploy organization VDC network' in e_info

    resource = mock.Mock()
    resource.task_successful.side_effect = VcdTaskException(
        400,
        {
            'message': 'is busy, cannot proceed with the operation',
            'minorErrorCode': 400
        })
    with pytest.raises(OperationRetry) as e_info:
        check_if_task_successful(resource, task)
        assert 'is busy, cannot proceed with the operation' in e_info
