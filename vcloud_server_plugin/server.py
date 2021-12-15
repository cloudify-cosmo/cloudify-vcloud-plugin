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

from cloudify.decorators import operation
from cloudify_vcd.legacy.compute.tasks import (
    # configure_server,
    postconfigure_nic,
    preconfigure_nic,
    power_off_vapp,
    delete_server,
    create_server,
    start_server,
    stop_server,
    delete_vapp,
    unlink_nic,
    stop_vapp,
)


@operation(resumable=True)
def create(*args, **kwargs):
    create_server(*args, **kwargs)


@operation(resumable=True)
def configure(*args, **kwargs):
    preconfigure_nic(*args, **kwargs)
    # configure_server(*args, **kwargs)
    postconfigure_nic(*args, **kwargs)
    ctx = kwargs['ctx']
    nic = None
    data = ctx.instance.runtime_properties.get('data', {})
    for nic in data.get('nics', []):
        if nic['primary'] == 'true':
            break
    if nic:
        ctx.logger.info('Found primary IP address.')
        ctx.instance.runtime_properties['ip'] = nic['ip_address']
        ctx.instance.runtime_properties['ip_address'] = nic['ip_address']
        ctx.instance.runtime_properties['private_ip_address'] = \
            nic['ip_address']
        ctx.logger.info('Assigned ip properties to ip address {}'.format(
            nic['ip_address']))


@operation(resumable=True)
def postconfigure(*args, **kwargs):
    pass


@operation(resumable=True)
def start(*args, **kwargs):
    start_server(*args, **kwargs)


@operation(resumable=True)
def stop(*args, **kwargs):
    stop_server(*args, **kwargs)
    unlink_nic(*args, **kwargs)
    stop_vapp(*args, **kwargs)
    power_off_vapp(*args, **kwargs)


@operation(resumable=True)
def delete(*args, **kwargs):
    delete_server(*args, **kwargs)
    delete_vapp(*args, **kwargs)


@operation(resumable=True)
def creation_validation(*args, **kwargs):
    pass
