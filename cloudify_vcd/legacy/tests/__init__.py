# Copyright (c) 2014-21 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from cloudify.manager import DirtyTrackingDict
from cloudify.mocks import MockNodeContext, MockCloudifyContext


class CorrectedMockNodeContext(MockNodeContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_hierarchy = self.type


class CorrectedMockCloudifyContext(MockCloudifyContext):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        node_name = kwargs.get('node_name')
        properties = kwargs.get('properties')
        node_type = kwargs.get('node_type')
        self._node = CorrectedMockNodeContext(
            node_name, properties, node_type)
        self.type_hierarchy = self.type


DEFAULT_NODE_PROPS = {
    'use_external_resource': False,
    'resource_id': '',
    'vcloud_config': {
        'username': 'taco',
        'password': 'secret',
        'token': None,
        'url': 'protocol://subdomain.domain.com/endpoint/version/resource',
        'instance': None,
        'vdc': 'vdc',
        'org': 'org',
        'service_type': None,
        'service': None,
        'api_version': '1.0',
        'org_url': None,
        'edge_gateway': None,
        'ssl_verify': True,
    }
}


def create_ctx(node_id,
               node_type,
               node_properties,
               runtime_props=None,
               operation_name=None,
               relationships=None):
    """
    Create a Mock Context.

    :param node_id:
    :param node_type:
    :param node_properties:
    :param runtime_props:
    :param operation_name:
    :param relationships:
    :return:
    """

    runtime_props = runtime_props or {}
    type_hierarchy = ['cloudify.nodes.Root']
    type_hierarchy.extend(node_type)
    operation_name = operation_name or 'cloudify.interfaces.lifecycle.create'
    operation = {
        'name': operation_name,
        'retry': 0,
    }
    tenant = {
        'name': 'footen',
    }
    mock_ctx = CorrectedMockCloudifyContext(
        node_id=node_id,
        node_name=node_id,
        node_type=node_type,
        blueprint_id='fooblu',
        deployment_id='foodep',
        properties=node_properties,
        runtime_properties=DirtyTrackingDict(runtime_props),
        relationships=relationships,
        operation=operation,
        tenant=tenant,
    )
    return mock_ctx
