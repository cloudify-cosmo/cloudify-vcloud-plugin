from copy import deepcopy

from pyvcloud.vcd.utils import task_to_dict
from lxml.objectify import (
    IntElement,
    BoolElement,
    StringElement,
    ObjectifiedElement)
from pyvcloud.vcd.exceptions import (
    VcdTaskException,
    NotFoundException,
    EntityNotFoundException,
    InternalServerException,
    AccessForbiddenException,
)

from cloudify import ctx
from cloudify.constants import (
    NODE_INSTANCE,
    RELATIONSHIP_INSTANCE)
from cloudify.exceptions import (
    OperationRetry,
    NonRecoverableError)

from vcd_plugin_sdk.connection import VCloudConnect
from .constants import (
    CLIENT_CONFIG_KEYS,
    CLIENT_CREDENTIALS_KEYS,
    TYPE_MATRIX,
    NO_RESOURCE_OK)


class ResourceData(object):

    def __init__(self,
                 context,
                 external,
                 resource_id,
                 client_config,
                 vdc,
                 resource_config,
                 resource_class):
        self._resources = []
        self.add(
            context,
            external,
            resource_id,
            client_config,
            vdc,
            resource_config,
            resource_class)

    @property
    def primary(self):
        return self._return_resource_args(0)

    @property
    def secondary(self):
        if len(self._resources) == 2:
            return self._return_resource_args(1)
        return

    @property
    def primary_id(self):
        return self._resources[0].get('id')

    @property
    def primary_class(self):
        return self._resources[0].get('class')

    @property
    def primary_client(self):
        return self._resources[0].get('client')

    @property
    def primary_ctx(self):
        return self._resources[0].get('ctx')

    @property
    def primary_external(self):
        return self._resources[0].get('external')

    @property
    def primary_vdc(self):
        return self._resources[0].get('vdc')

    @property
    def primary_resource(self):
        return self.primary_class(self.primary_id,
                                  connection=self.primary_client)

    def add(self,
            context,
            external,
            resource_id,
            client_config,
            vdc,
            resource_config,
            resource_class):
        self._resources.append(
            {'external': external,
             'id': resource_id,
             'client': client_config,
             'vdc': vdc,
             'config': resource_config,
             'ctx': context,
             'class': resource_class})

    def _return_resource_args(self, index):
        return [self._resources[index].get('external'),
                self._resources[index].get('id'),
                self._resources[index].get('client'),
                self._resources[index].get('vdc'),
                self._resources[index].get('config'),
                self._resources[index].get('class'),
                self._resources[index].get('ctx')]


def is_relationship(_ctx=None):
    _ctx = _ctx or ctx
    return _ctx.type == RELATIONSHIP_INSTANCE


def is_node_instance(_ctx=None):
    _ctx = _ctx or ctx
    return _ctx.type == NODE_INSTANCE


def get_resource_config(node, instance):
    return instance.get('resource_config', node.get('resource_config'))


def is_external_resource(node, instance):
    external_node = node.get('use_external_resource', False)
    bad_request_retry = instance.get(
        '__RETRY_BAD_REQUEST', False)
    if external_node:
        return external_node
    elif not bad_request_retry and ctx.operation.retry_number:
        return True
    return False


def get_resource_id(node, instance, instance_id=None):
    return instance.get('resource_id', node.get('resource_id', instance_id))


def get_client_config(node):
    client_config = node.get('client_config', {})
    vdc = client_config.get('vdc')

    def _get_config():
        d = {}
        for key in CLIENT_CONFIG_KEYS:
            d[key] = client_config.get(key)
        d.update(client_config.get('configuration_kwargs', dict()))
        return d

    def _get_creds():
        d = {}
        for key in CLIENT_CREDENTIALS_KEYS:
            d[key] = client_config.get(key)
        d.update(client_config.get('credentials_kwargs', dict()))
        return d

    return VCloudConnect(ctx.logger, _get_config(), _get_creds()), vdc


def get_ctxs(_ctx):
    """
    Get the current context(s).

    :param param:
    :return: Either the ctx, or the ctx.source and ctx.target
    """

    _ctx = _ctx or ctx

    if is_relationship(_ctx):
        try:
            target_interface = _ctx._context['related']['is_target']
        except KeyError:
            raise NonRecoverableError(
                'The management worker is using a version of '
                'Cloudify Common incompatible with this plugin.')
        if target_interface:
            return _ctx.source, _ctx.target
        return _ctx.target, _ctx.source
    elif is_node_instance(_ctx):
        return _ctx, None
    else:
        raise Exception('Bad ctx type: {bad_type}.'.format(bad_type=_ctx.type))


def get_resource_class(type_hierarchy):
    for hierarchy_item in type_hierarchy:
        if hierarchy_item in TYPE_MATRIX:
            return TYPE_MATRIX.get(hierarchy_item)
    raise NonRecoverableError(
        'A resource type matching node hierarchy {h} not found. '
        'Use one of {t}, or derive type from those types.'.format(
            h=type_hierarchy, t=TYPE_MATRIX.keys()))


def get_resource_data(__ctx):
    """Initialize the ctx, resource id, client config, vdc, resource config
    for the node instance resource or both relationship resources.
    Primary = Node Template Node Instance or Relationship Source
    Secondary = Relationship Target if applicable.

    :param __ctx: ctx from operation
    :return: list of tuple where tuple contains a resource ctx, ID,
    client config, VDC string and resource config.
    """
    primary, secondary = get_ctxs(__ctx)
    primary_resource_id = get_resource_id(
        primary.node.properties,
        primary.instance.runtime_properties,
        primary.instance.id)
    primary_external = is_external_resource(
        primary.node.properties,
        primary.instance.runtime_properties)
    primary_client_config, primary_vdc = get_client_config(
        primary.node.properties)
    primary_resource_config = get_resource_config(
        primary.node.properties, primary.instance.runtime_properties)
    classes = get_resource_class(primary.node.type_hierarchy)

    base_properties = ResourceData(
        primary,
        primary_external,
        primary_resource_id,
        primary_client_config,
        primary_vdc,
        primary_resource_config,
        classes[0])
    if secondary:
        secondary_resource_id = get_resource_id(
            secondary.node.properties,
            secondary.instance.runtime_properties,
            secondary.instance.id)
        secondary_external = is_external_resource(
            secondary.node.properties,
            secondary.instance.runtime_properties)
        secondary_client_config, secondary_vdc = get_client_config(
            secondary.node.properties)
        secondary_resource_config = get_resource_config(
            secondary.node.properties, secondary.instance.runtime_properties)
        if len(classes) == 1:
            secondary_class = None
        else:
            secondary_class = classes[1]
        base_properties.add(
            secondary,
            secondary_external,
            secondary_resource_id,
            secondary_client_config,
            secondary_vdc,
            secondary_resource_config,
            secondary_class)
    return base_properties


def update_runtime_properties(current_ctx, props):
    props = cleanup_objectify(props)
    ctx.logger.debug('Updating instance with properties {props}.'.format(
        props=props))

    if is_relationship(current_ctx):
        if current_ctx.instance.id == ctx.source.instance.id:
            ctx.source.instance.runtime_properties.update(props)
            ctx.source.instance.runtime_properties.dirty = True
            ctx.source.instance.update()
        elif current_ctx.instance.id == ctx.target.instance.id:
            ctx.target.instance.runtime_properties.update(props)
            ctx.target.instance.runtime_properties.dirty = True
            ctx.target.instance.update()
        else:
            ctx.logger.error(
                'Error updating instance {_id} props {props}.'.format(
                    _id=current_ctx.instance.id, props=props))
    elif is_node_instance():
        ctx.instance.runtime_properties.update(props)
        ctx.instance.runtime_properties.dirty = True
        ctx.instance.update()


def cleanup_runtime_properties(current_ctx):
    ctx.logger.debug('Cleaning instance {_id} props.'.format(
        _id=current_ctx.instance.id))
    if is_relationship():
        if current_ctx.instance.id == ctx.source.instance.id:
            for key in list(ctx.source.instance.runtime_properties.keys()):
                del ctx.source.instance.runtime_properties[key]
            ctx.source.instance.runtime_properties.dirty = True
            ctx.source.instance.update()
        elif current_ctx.instance.id == ctx.target.instance.id:
            for key in list(ctx.target.instance.runtime_properties.keys()):
                del ctx.target.instance.runtime_properties[key]
            ctx.target.instance.runtime_properties.dirty = True
            ctx.target.instance.update()
        else:
            ctx.logger.error(
                'Error deleting instance {_id} props.'.format(
                    _id=current_ctx.instance.id))
    elif is_node_instance():
        for key in list(ctx.instance.runtime_properties.keys()):
            del ctx.instance.runtime_properties[key]
        ctx.instance.runtime_properties.dirty = True
        ctx.instance.update()


def cleanup_objectify(data):
    # For dev purposes, lets log all this:
    # TODO: Remove eventually, or find a cleaner way to get as much
    # info as we can. Because I envision this being a problematic
    # bit of code.
    ctx.logger.debug('Logging data {} {}'.format(data, type(data)))
    ctx.logger.debug('Text: {}'.format(getattr(data, 'text', None)))
    ctx.logger.debug('Pyval: {}'.format(getattr(data, 'pyval', None)))
    if hasattr(data, 'items'):
        ctx.logger.debug('Items: {}'.format(data.items()))
    try:
        if hasattr(data, 'child'):
            ctx.logger.debug('Child: {} {}'.format(
                data.child, type(data.child)))
        if hasattr(data, 'iterchildren'):
            ctx.logger.debug('iterchildren: {} {}'.format(
                data.iterchildren(),
                [type(child) for child in data.iterchildren()]
            ))
    except (AttributeError, TypeError):
        pass

    data = deepcopy(data)

    if isinstance(data, (str, int, bool)):
        return data
    elif isinstance(data, (BoolElement, StringElement, IntElement)):
        return data.text
    if isinstance(data, tuple):
        if len(data) == 2:
            return {str(data[0]): data[1]}
        else:
            return list(data)
    elif isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[str(k)] = cleanup_objectify(v)
        return new_data
    elif isinstance(data, list):
        for n in range(0, len(data)):
            data[n] = cleanup_objectify(data[n])
        return data
    elif isinstance(data, ObjectifiedElement):
        if hasattr(data, 'iterchildren'):
            new_data = {}
            for child in data.iterchildren():
                if hasattr(child, 'pyval'):
                    new_data[child.tag] = cleanup_objectify(child.pyval)
                else:
                    new_data[child.tag] = cleanup_objectify(child)
            return new_data
        elif not hasattr(data, 'child') and data.text:
            return data.text
    return data


def find_rels_by_type(node_instance, rel_type):
    '''
        Finds all specified relationships of the Cloudify
        instance.
    :param `cloudify.context.NodeInstanceContext` node_instance:
        Cloudify node instance.
    :param str rel_type: Cloudify relationship type to search
        node_instance.relationships for.
    :returns: List of Cloudify relationships
    '''
    return [x for x in node_instance.relationships
            if rel_type in x.type_hierarchy]


def find_rel_by_type(node_instance, rel_type):
    rels = find_rels_by_type(node_instance, rel_type)
    if len(rels) == 1:
        return rels[0]
    return


def find_resource_id_from_relationship_by_type(node_instance, rel_type):
    rel = find_rel_by_type(node_instance, rel_type)
    if rel:
        return rel.target.instance.runtime_properties.get('resource_id')


def use_external_resource(external,
                          resource,
                          override,
                          resource_type,
                          resource_name):

    if not external:
        ctx.logger.debug(
            'The {t} {r} is not external. '
            'Proceeding with operation.'.format(
                t=resource_type, r=resource_name))
        return False

    elif external and not resource and override:
        ctx.logger.debug(
            'The {t} {r} is external, but does not exist, '
            'proceeding with operation, because override is True.'.format(
                t=resource_type, r=resource_name))
        return False

    elif external and resource:
        ctx.logger.debug(
            'The {t} {r} is external, and does exist, '
            'not proceeding with operation.'.format(
                t=resource_type, r=resource_name))
        return True

    else:
        raise NonRecoverableError(
            'The {r} {t} is external, '
            'but does not exist and override is False.'.format(
                t=resource_type, r=resource_name))


def expose_props(operation_name, resource=None, new_props=None, _ctx=None):
    _ctx = _ctx or ctx
    new_props = new_props or {}

    if 'create' in operation_name:
        new_props.update({'__created': True})
    elif 'delete' in operation_name:
        new_props.update({'__deleted': True})
        cleanup_runtime_properties(ctx)

    if resource and operation_name not in NO_RESOURCE_OK:
        try:
            new_props.update({
                'resource_id': resource.name,
                'data': resource.exposed_data,
                'tasks': resource.tasks,
            })
        except EntityNotFoundException:
            raise NonRecoverableError(
                'The resource {n} was not found.'.format(n=resource.name))

    # expose props is called after a successful operation,
    # so we should override this if we reach this point.
    new_props.update({'__RETRY_BAD_REQUEST': False})
    update_runtime_properties(_ctx, new_props)


def get_last_task(task):
    try:
        return task_to_dict(task.Tasks.Task[0])
    except AttributeError:
        return task


def vcd_busy_exception(exc):
    if 'is busy, cannot proceed with the operation' in str(exc):
        return True
    elif 'cannot be deleted, because it is in use' in str(exc):
        return True
    return False


# Not tested - why should we?
def vcd_unclear_exception(exc):
    if 'Status code: 400/None, None' in str(exc):
        return True
    if isinstance(exc, AccessForbiddenException):
        return True
    return False


# Not tested - why should we?
def vcd_already_exists(exc):
    if 'DUPLICATE_NAME' in str(exc):
        return True
    return False


# Not tested - why should we?
def vcd_unresolved_vm(exc):
    if 'Unresolved' in str(exc):
        return True
    return False


def cannot_deploy(exc):
    if 'Cannot deploy organization VDC network' in str(exc):
        return True
    return False


# Not tested - why should we?
def cannot_power_off(exc):
    if 'Current state of vm: Powered off' in str(exc):
        return True
    elif 'RelationType.POWER_OFF' in str(exc):
        return True
    elif 'is not powered on' in str(exc):
        return True
    return False


# Not tested - why should we?
def task_on_failure(exc):
    if 'Unable to perform this action. ' \
       'Contact your cloud administrator' in str(exc):
        return True
    return False


def invalid_resource(exc):
    if 'target entity is invalid' in str(exc):
        return True
    return False


def uninitialized(exc):
    if 'has not been initialized' in str(exc):
        return True
    return False


def bad_vm_name(exc):
    if 'Computer name can only contain' in str(exc):
        return True
    return False


def no_powered_on_vms(exc):
    if 'not have any powered on VMs' in str(exc):
        return True
    return False


def retry_or_raise(e, r, operation_name):
    """ When we call func in the decorator, we catch some exceptions.
    This function determines whether to raise or retry.

    :param e: the exception object
    :param r: the resource_data object from the decorator
    :param operation_name: ctx.operation.name.split('.')[-1]
    :return:
    """
    # TODO: Determine if MissingLinkException is retry or ignore.
    if isinstance(e, (TypeError,
                      AttributeError,
                      NotFoundException,
                      EntityNotFoundException,
                      InternalServerException,
                      AccessForbiddenException)):
        if operation_name not in NO_RESOURCE_OK:
            raise NonRecoverableError(
                'The expected resource {r} does not exist. {e}'.format(
                    r=r.primary_id, e=e))
        ctx.logger.error(
            'Attempted to perform {op} operation on {r}, '
            'but the resource was not found.'.format(
                op=operation_name, r=r.primary_id))
    elif vcd_busy_exception(e) or vcd_unclear_exception(e) or uninitialized:
        r.primary_ctx.instance.runtime_properties['__RETRY_BAD_REQUEST'] = True
        r.primary_ctx.instance.update()
        raise OperationRetry(str(e))


def check_if_task_successful(_resource, task):
    if isinstance(task, ObjectifiedElement):
        ctx.logger.debug('Task: {task}'.format(task=task.items()))
        try:
            return _resource.task_successful(task)
        except VcdTaskException as e:
            if cannot_deploy(e) or task_on_failure(e):
                raise NonRecoverableError(str(e))
            raise OperationRetry(
                'Unhandled state validation error: {e}.'.format(e=str(e)))
    return True


def expose_ip_property(nics):
    ip_addresses = ctx.instance.runtime_properties.get('ip_addresses', [])
    for nic in nics:
        if nic['primary']:
            ctx.instance.runtime_properties['ip'] = nic['ip_address']
            ctx.instance.runtime_properties['public_ip_address'] = \
                nic['ip_address']
            ctx.instance.runtime_properties['private_ip_address'] = \
                nic['ip_address']
            ctx.instance.runtime_properties['ipv4_address'] = \
                nic['ip_address']
        if nic['ip_address'] not in ip_addresses:
            ip_addresses.append(nic['ip_address'])
    ctx.instance.runtime_properties['ip_addresses'] = ip_addresses
    ctx.instance.runtime_properties['ipv4_addresses'] = ip_addresses
