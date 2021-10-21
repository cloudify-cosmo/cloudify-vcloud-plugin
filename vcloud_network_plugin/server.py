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
    create_server,
    configure_server,
    start_server,
    stop_sterver,
    delete_server)


@operation(resumable=True)
def create(*args, **kwargs):
    create_server(*args, **kwargs)


@operation(resumable=True)
def configure(*args, **kwargs):
    configure_server(*args, **kwargs)


@operation(resumable=True)
def start(*args, **kwargs):
    start_server(*args, **kwargs)


@operation(resumable=True)
def stop(*args, **kwargs):
    stop_sterver(*args, **kwargs)


@operation(resumable=True)
def delete(*args, **kwargs):
    delete_server(*args, **kwargs)


@operation(resumable=True)
def creation_validation(*args, **kwargs):
    pass
