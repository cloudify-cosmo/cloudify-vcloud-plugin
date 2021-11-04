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

from time import sleep

from pyvcloud.vcd.vm import VM
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.exceptions import (
    VcdTaskException,
    BadRequestException,
    EntityNotFoundException,
    OperationNotSupportedException)

from .base import VCloudResource
from .network import VCloudNetwork
from ..exceptions import VCloudSDKException

POWER_STATES = (
    (8, 'powered off'),
    (4, 'powered on'),
    (3, 'suspended')
)


class VCloudvApp(VCloudResource):

    def __init__(self,
                 vapp_name,
                 connection=None,
                 vdc_name=None,
                 kwargs=None,
                 tasks=None):

        self.kwargs = kwargs or {}
        if 'name' in self.kwargs:
            del self.kwargs['name']
        super().__init__(connection, vdc_name, vapp_name, tasks=tasks)
        self.vapp_name = self._vapp_name
        self._vapp = None

    @property
    def name(self):
        return self._vapp_name

    @property
    def vapp(self):
        if self._vapp:
            self._vapp.reload()
        else:
            self._vapp = self.get_vapp(self.vapp_name)
        return self._vapp

    @property
    def networks(self):
        try:
            vapp_networks = self.vapp.get_all_networks()
            return [nw.values()[0] for nw in vapp_networks]
        except (AttributeError, IndexError):
            return []

    @property
    def exposed_data(self):
        return {
            'lease': self.get_lease(),
            'catalog_items': self.get_catalog_items(),
            'resources': self.vdc.list_resources()
        }

    def get_catalogs(self):
        return self.connection.org.list_catalogs()

    def get_catalog_items(self):
        items = {}
        for catalog in self.get_catalogs():
            catalog_name = catalog.get('name')
            if catalog_name not in items:
                items[catalog_name] = {}
            c = self.connection.org.get_catalog(catalog_name)
            if hasattr(c.CatalogItems, 'CatalogItem'):
                items[catalog_name][
                    c.CatalogItems.CatalogItem.get('name')] = \
                    c.CatalogItems.CatalogItem.items()
        return items

    def get_vapp(self, vapp_name=None):
        vapp_resource = self.vdc.get_vapp(vapp_name)
        return VApp(self.client, resource=vapp_resource)

    def instantiate_vapp(self):
        task = self.vdc.instantiate_vapp(name=self.name, **self.kwargs)
        self.tasks['create'].append(task.items())
        return task

    def delete(self):
        task = self.vdc.delete_vapp(self.vapp_name)
        self.tasks['delete'].append(task.items())
        return task

    def power_on(self, vapp_name=None):
        if not vapp_name:
            self.vapp.power_on()
        else:
            vapp = self.get_vapp(vapp_name)
            vapp.power_on()

    def power_off(self, vapp_name=None):
        if not vapp_name:
            self.vapp.power_off()
        else:
            vapp = self.get_vapp(vapp_name)
            vapp.power_off()

    def shutdown(self, vapp_name=None):
        if not vapp_name:
            self.vapp.shutdown()
        else:
            vapp = self.get_vapp(vapp_name)
            vapp.shutdown()

    def deploy(self, vapp_name=None, power_on=True, force_customization=False):
        if not vapp_name:
            self.vapp.deploy(power_on, force_customization)
        else:
            vapp = self.get_vapp(vapp_name)
            vapp.deploy(power_on, force_customization)

    def undeploy(self, vapp_name=None, action='default'):
        if not vapp_name:
            self.vapp.undeploy(action)
        else:
            vapp = self.vapp.get_vm(vapp_name)
            vapp.vapp.undeploy(action)

    # TODO: Not Tested/Not Used
    # def delete_vms(self, vm_names):
    #     return self.vapp.delete_vms(vm_names)
    #
    def add_network(self, **kwargs):
        self.logger.info('We have these direct networks: {}'.format(
            self.vdc.list_orgvdc_direct_networks()))
        self.logger.info('We have these routed networks: {}'.format(
            self.vdc.list_orgvdc_routed_networks()))
        self.logger.info('We have these isolated networks: {}'.format(
            self.vdc.list_orgvdc_isolated_networks()))
        bad_networks_exc = (BadRequestException, OperationNotSupportedException)
        try:
            task = self.vapp.connect_org_vdc_network(
                kwargs['orgvdc_network_name'])
        except bad_networks_exc as e:
            self.logger.info('Using just name did not work. {}'.format(e))
        # if kwargs.get('fence_mode') not in ['bridged',
        #                                     'isolated',
        #                                     'natRouted']:
        #     kwargs.pop('fence_mode', None)
        #     kwargs['is_deployed'] = True
        fence_mode = [kwargs.get('fence_mode')]
        fence_mode.extend(['bridged', 'isolated', 'natRouted'])
        ee = None
        for mode in fence_mode:
            ee = None
            kwargs['fence_mode'] = mode
            self.logger.info('kwargs {}'.format(kwargs))
            try:
                task = self.vapp.connect_org_vdc_network(**kwargs)
            except bad_networks_exc as e:
                ee = e
                self.logger.error(e)
                self.logger.info('Using fence mode {} did not work.'
                                 .format(mode))
                sleep(5)
                continue

        if ee:
            kwargs['is_deployed'] = True
            for mode in fence_mode:
                ee = None
                kwargs['fence_mode'] = mode
                self.logger.info('kwargs {}'.format(kwargs))
                try:
                    task = self.vapp.connect_org_vdc_network(**kwargs)
                except bad_networks_exc as e:
                    ee = e
                    self.logger.error(e)
                    self.logger.info(
                        'Using fence mode {} did not work with is_deployed.'
                        .format(mode))
                    sleep(5)
                    continue
        if ee:
            raise ee

        self.logger.info('These worked {}'.format(kwargs))

        if 'add_network' in self.tasks:
            self.tasks['add_network'].append(task)
        else:
            self.tasks['add_network'] = [task]
        return task

    def remove_network(self, network_name):
        task = self.vapp.disconnect_org_vdc_network(network_name)
        if 'remove_network' in self.tasks:
            self.tasks['remove_network'].append(task)
        else:
            self.tasks['remove_network'] = [task]
        return task

    def set_lease(self, deployment_lease=0, storage_lease=0):
        self.vapp.set_lease(deployment_lease, storage_lease)

    def get_lease(self):
        try:
            return self.vapp.get_lease()
        except EntityNotFoundException:
            return


class VCloudVM(VCloudResource):

    def __init__(self,
                 vm_name,
                 vapp_name,
                 connection=None,
                 vdc_name=None,
                 kwargs=None,
                 vapp_kwargs=None,
                 tasks=None):

        self._vm_name = vm_name
        self.kwargs = kwargs or {}
        super().__init__(connection, vdc_name, vapp_name)
        self.vapp_object = VCloudvApp(vapp_name,
                                      connection,
                                      vdc_name=vdc_name,
                                      kwargs=vapp_kwargs,
                                      tasks=tasks)
        self._vm = None

    @property
    def name(self):
        return self._vm_name

    @property
    def vm(self):
        if not self._vm:
            self._vm = self.get_vm(self.name)
        else:
            self._vm.reload()
        return self._vm

    @property
    def exists(self):
        try:
            return self.vm
        except EntityNotFoundException:
            pass
        return False

    @property
    def nics(self):
        return self.vm.list_nics()

    def _get_data(self):
        return {
            'cpus': self.vm.get_cpus(),
            'memory': self.vm.get_memory(),
            'nics': self.nics,
        }

    @property
    def vapp_networks(self):
        return self.vapp_object.networks

    @property
    def exposed_data(self):
        data = {
            'vapp': self.vapp_object.name
        }
        for n in range(0, 5):
            try:
                data.update(self._get_data())
            except AttributeError:
                sleep(1)
        return data

    def get_vm(self, vm_name):
        vm_resource = self.vapp_object.vapp.get_vm(vm_name)
        vm = VM(self.client, resource=vm_resource)
        return vm

    def add_vm(self, new_vm_name):
        # TODO: Find the right way to get the original template.
        # Document clearly how to share a VAPP with multiple VMs.
        # ETC ETC
        # This should also be used for auto-scaling.
        # How will NICS work?
        task = self.vapp.add_vms(
            [{'vapp': self.vapp_object.vapp.resource,
              'source_vm_name': self.name,
              'target_vm_name': new_vm_name}]
        )
        self.tasks['create'].append(task.items())
        return task

    def instantiate_vapp(self):
        task = self.vapp_object.instantiate_vapp()
        self.tasks['create'].append(task[-1])
        return task

    def delete(self, vm_name=None):
        # TODO: This can be refactored:
        # To support bulk delete of VMs using vapp.delete_vms([names])
        vm = self.get_vm(vm_name or self.name)
        task = vm.delete()
        self.tasks['delete'].append(task)
        return task

    def check_network(self, name, type):
        network = VCloudNetwork(name, type, self.connection, self.vdc.name)
        try:
            return network.get_network()
        except VCloudSDKException:
            return

    def power_on(self, vm_name=None):
        if not vm_name:
            task = self.vm.power_on()
        else:
            vm = self.get_vm(vm_name)
            task = vm.power_on()
        self.tasks['update'].append(task)
        return task

    def power_off(self, vm_name=None):
        if not vm_name:
            task = self.vm.power_off()
        else:
            vm = self.get_vm(vm_name)
            task = vm.power_off()
        self.tasks['update'].append(task)
        return task

    def shutdown(self, vm_name=None):
        if not vm_name:
            task = self.vm.shutdown()
        else:
            vm = self.get_vm(vm_name)
            task = vm.shutdown()
        self.tasks['update'].append(task)
        return task

    def deploy(self, vm_name=None, power_on=True, force_customization=False):
        if not vm_name:
            task = self.vm.deploy(power_on, force_customization)
        else:
            vm = self.get_vm(vm_name)
            task = vm.deploy(power_on, force_customization)
        self.tasks['update'].append(task)
        return task

    def undeploy(self, vm_name=None, action='default'):
        if not vm_name:
            task = self.vm.undeploy(action)
        else:
            vm = self.get_vm(vm_name)
            task = vm.undeploy(action)
        self.tasks['update'].append(task)
        return task

    def attach_disk_to_vm(self, disk_href, vm_name=None):
        return self.vapp.attach_disk_to_vm(disk_href, vm_name or self.name)

    def detach_disk_from_vm(self, disk_href, vm_name=None):
        return self.vapp.detach_disk_from_vm(
            disk_href, vm_name or self.name)

    def add_nic(self, **kwargs):
        task = self.vm.add_nic(**kwargs)
        if 'add_nic' in self.tasks:
            self.tasks['add_nic'].append(task)
        else:
            self.tasks['add_nic'] = [task]
        return task

    def delete_nic(self, index):
        task = self.vm.delete_nic(index)
        if 'remove_nic' in self.tasks:
            self.tasks['remove_nic'].append(task)
        else:
            self.tasks['remove_nic'] = [task]
        return task

    # TODO: Untested/Unused.
    # def update_nic(self, **kwargs):
    #     task = self.vm.update_nic(**kwargs)
    #     if 'update_nic' in self.tasks:
    #         self.tasks['update_nic'].append(task)
    #     else:
    #         self.tasks['update_nic'] = [task]
    #     return task

    def attach_media(self, media_id):
        task = self.vm.insert_cd_from_catalog(media_id)
        if 'media' in self.tasks:
            self.tasks['media'].append(task)
        else:
            self.tasks['media'] = [task]
        return task

    def eject_media(self, media_id):
        task = self.vm.eject_cd(media_id)
        if 'media' in self.tasks:
            self.tasks['media'].append(task)
        else:
            self.tasks['media'] = [task]
        return task

    def task_successful(self, task):
        """ Check if a VCD task succeeded.

        :param task: Element {http://www.vmware.com/vcloud/v1.5}Task object
        :return: bool
        """
        # task = json.loads(task_string)  # If task contains non-JSON
        # serializable material, we will need to start encoding and decoding.
        # Leaving this commented out for now.
        try:
            result = self.client.get_task_monitor().wait_for_success(
                task, 10)
        except VcdTaskException as e:
            self.logger.info('Failed to validate task status {e}.'.format(e=e))
            return False
        # Return True if the API says the task succeeded.
        return self.vm.is_powered_on() and \
            result.get('status') == TaskStatus.SUCCESS.value

    def add_vapp_network(self, **kwargs):
        return self.vapp_object.add_network(**kwargs)

    def remove_vapp_network(self, network_name):
        return self.vapp_object.remove_network(network_name)

    def get_nic_from_config(self, nic_config):
        for nic in self.nics:
            if nic['ip_address'] == nic_config['ip_address']:
                return nic
