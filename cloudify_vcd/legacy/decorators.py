# Copyright (c) 2020 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from functools import wraps

from cloudify.exceptions import OperationRetry
from cloudify_common_sdk.utils import get_ctx_node, get_ctx_instance

from . import utils
from ..utils import (get_last_task, check_if_task_successful)


def with_vcd_client():
    def wrapper_outer(func):
        @wraps(func)
        def wrapper_inner(*args, **kwargs):
            """
            Initializes the connection object from vcloud_config.
            :param args:
            :param kwargs: From vcloud_config property.
            :return:
            """
            ctx = kwargs.get('ctx')
            _ctx_node = get_ctx_node()
            if 'vcloud_config' not in kwargs:
                kwargs['vcloud_config'] = _ctx_node.properties['vcloud_config']
            kwargs['vcloud_cx'] = utils.get_vcloud_cx(
                kwargs['vcloud_config'], ctx.logger)
            resource, result = utils.get_function_return(func(*args, **kwargs))
            last_task = get_last_task(result)
            ctx_instance = get_ctx_instance(ctx)
            if not check_if_task_successful(resource, last_task):
                ctx_instance.runtime_properties['__RETRY_BAD_REQUEST'] = True
                raise OperationRetry('Pending for operation completion.')
        return wrapper_inner
    return wrapper_outer


def with_network_resource():
    def wrapper_outer(func):
        @wraps(func)
        def wrapper_inner(*args, **kwargs):
            """
            Initializes the network object with connection and the translated
                configuration from network property.
            :param args:
            :param kwargs:
            :return:
            """
            _ctx_node = get_ctx_node()
            if 'network' not in kwargs:
                kwargs['network'] = _ctx_node.properties['network']
            client = utils.get_network_client(**kwargs)
            kwargs['network_client'] = client
            return func(*args, **kwargs)
        return wrapper_inner
    return wrapper_outer


def with_gateway_resource():
    def wrapper_outer(func):
        @wraps(func)
        def wrapper_inner(*args, **kwargs):
            """
            Initializes the gateway object with connection and the translated
                configuration from network property.
            :param args:
            :param kwargs:
            :return:
            """
            client = utils.get_gateway_client(**kwargs)
            kwargs['gateway_client'] = client
            return func(*args, **kwargs)
        return wrapper_inner
    return wrapper_outer


def with_vm_resource():
    def wrapper_outer(func):
        @wraps(func)
        def wrapper_inner(*args, **kwargs):
            """
            Initializes the gateway object with connection and the translated
                configuration from network property.
            :param args:
            :param kwargs:
            :return:
            """
            client = utils.get_vm_client(**kwargs)
            kwargs['vm_client'] = client
            return func(*args, **kwargs)
        return wrapper_inner
    return wrapper_outer
