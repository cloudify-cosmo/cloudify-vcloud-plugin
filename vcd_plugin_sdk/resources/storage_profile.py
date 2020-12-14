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

from .base import VCloudResource

# CURRENTLY THIS ISNT USED :)
raise Exception('This section is not tested.')


class VCloudStorageProfile(VCloudResource):

    def __init__(self,
                 profile_name,
                 connection=None,
                 vdc_name=None,
                 kwargs=None,
                 tasks=None):

        self._profile_name = profile_name
        self.kwargs = kwargs or {}
        if 'name' in self.kwargs:
            del self.kwargs['name']
        super().__init__(connection, vdc_name, tasks=tasks)

    @property
    def name(self):
        return self._profile_name

    @property
    def storage_profile(self):
        return self.get_storage_profile()

    @property
    def exposed_data(self):
        return {}

    def get_storage_profile(self, profile_name=None):
        return self.vdc.get_storage_profile(profile_name or self.name)

    def create(self):
        task = self.vdc.add_storage_profile(self.name, **self.kwargs)
        self.tasks['create'].append(task.items())
        return task

    def delete(self, profile_name=None):
        task = self.vdc.remove_storage_profile(profile_name or self.name)
        self.tasks['delete'].append(task.items())
        return task

    def update(self, profile_name=None, **kwargs):
        task = self.vdc.update_storage_profile(
            profile_name or self.name, **kwargs)
        self.tasks['update'].append(task.items())
        return task
