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

# TODO: We need to add add_network, add_nic, and remove_nic, after we do VM.


@operation(resumable=True)
def creation_validation(port, *args, **kwargs):
    pass


@operation(resumable=True)
def delete(*args, **kwargs):
    pass
