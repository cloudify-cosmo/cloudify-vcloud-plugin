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


# import json  # See below.

from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.exceptions import EntityNotFoundException

from ..connection import VCloudConnect
from ..exceptions import VCloudSDKException


class VCloudResource(object):

    def __init__(self, connection, vdc_name, vapp_name=None, tasks=None):

        self._connection = connection or VCloudConnect()
        self.logger = self.connection.logger

        try:
            vdc_resource = self._connection.org.get_vdc(vdc_name)
        except EntityNotFoundException:
            self._vdc = None
        else:
            self._vdc = VDC(self._connection.client, resource=vdc_resource)

        self._vapp_name = vapp_name
        self._vapp = None
        self.tasks = tasks or {'create': [], 'delete': [], 'update': []}

    @property
    def client(self):
        return self._connection.client

    @property
    def connection(self):
        return self._connection

    @property
    def vdc(self):
        if self._vdc:
            self._vdc.reload()
        return self._vdc

    def task_successful(self, task):
        """ Check if a VCD task succeeded.

        :param task: Element {http://www.vmware.com/vcloud/v1.5}Task object
        :return: bool
        """
        # task = json.loads(task_string)  # If task contains non-JSON
        # serializable material, we will need to start encoding and decoding.
        # Leaving this commented out for now.
        result = self.client.get_task_monitor().wait_for_success(
            task, 10)
        # Return True if the API says the task succeeded.
        return result.get('status') == TaskStatus.SUCCESS.value

    @property
    def vapp(self):
        if not self._vapp_name:
            raise VCloudSDKException(
                'Attempt to access '
                'vcd_plugin_sdk.resources.base.VCloudResource.vapp, '
                'but no vapp_name was provided.')
        if not self._vapp:
            self._vapp = self.get_vapp(self._vapp_name)
        return self._vapp

    def get_vapp(self, vapp_name):
        vapp_name = vapp_name or self._vapp_name
        try:
            vapp_resource = self.vdc.get_vapp(vapp_name)
        except (EntityNotFoundException, AttributeError):
            return
        return VApp(self.client, resource=vapp_resource)

    def get_template(self, catalog_name, item_name):
        """Return the catalog object by name
        """
        return self.connection.org.get_catalog_item(catalog_name, item_name)
