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

from pyvcloud.vcd.vm import VM
from pyvcloud.vcd.vapp import VApp

from .base import VCloudResource


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
                 kwargs=None):

        self.kwargs = kwargs or {}
        if 'name' in self.kwargs:
            del self.kwargs['name']
        super().__init__(connection, vdc_name, vapp_name)
        self.vapp_name = self._vapp_name
        self._vapp = None
        self.tasks = {}

    @property
    def vapp(self):
        if self._vapp:
            self._vapp.reload()
        else:
            self._vapp = self.get_vapp(self.vapp_name)
        return self._vapp

    @property
    def exposed_data(self):
        return {
            'lease': self.get_lease()
        }

    def get_vapp(self, vapp_name):
        vapp_resource = self.vdc.get_vapp(vapp_name)
        return VApp(self.client, resource=vapp_resource)

    def create(self):
        task = self.vdc.create_vapp(self.vapp_name, **self.kwargs)
        if 'create' in self.tasks:
            self.tasks['create'].append(task.items())
        else:
            self.tasks['create'] = task.items()
        return self.tasks['create']

    def instantiate_vapp(self):
        task = self.vdc.instantiate_vapp(name=self.vapp_name, **self.kwargs)
        if 'create' in self.tasks:
            self.tasks['create'].append(task.items())
        else:
            self.tasks['create'] = [task.items()]
        return self.tasks['create']

    def delete(self):
        task = self.vdc.delete_vapp(self.vapp_name)
        self.tasks['delete'] = [task.items()]
        return self.tasks['delete']

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

    def add_network(self, **kwargs):
        task = self.vapp.connect_org_vdc_network(**kwargs)
        if 'add_network' in self.tasks:
            self.tasks['add_network'].append(task.items())
        else:
            self.tasks['add_network'] = [task.items()]
        return self.tasks['add_network']

    def remove_network(self, network_name):
        task = self.vapp.disconnect_org_vdc_network(network_name)
        if 'remove_network' in self.tasks:
            self.tasks['remove_network'].append(task.items())
        else:
            self.tasks['remove_network'] = [task.items()]
        return self.tasks['remove_network']

    def set_lease(self, deployment_lease=0, storage_lease=0):
        self.vapp.set_lease(deployment_lease, storage_lease)

    def get_lease(self):
        return self.vapp.get_lease()


class VCloudVM(VCloudResource):

    def __init__(self,
                 vm_name,
                 vapp_name,
                 connection=None,
                 vdc_name=None,
                 kwargs=None,
                 vapp_kwargs=None):

        self.vm_name = vm_name
        self.kwargs = kwargs or {}
        super().__init__(connection, vdc_name, vapp_name)
        self.vapp_object = VCloudvApp(vapp_name, vdc_name=vdc_name,kwargs=vapp_kwargs)
        self._vm = None
        self.tasks = {}

    @property
    def vm(self):
        if not self._vm:
            self._vm = self.get_vm(self.vm_name)
        else:
            self._vm.reload()
        return self._vm

    @property
    def nics(self):
        return self.vm.list_nics()

    def get_vm(self, vm_name):
        vm_resource = self.vapp.get_vm(vm_name)
        vm = VM(self.client, resource=vm_resource)
        return vm

    def create(self, kwargs=None):
        kwargs = kwargs or self.kwargs
        task = self.vapp.add_vms(**kwargs)
        if 'create' in self.tasks:
            self.tasks['create'].append(task.items())
        else:
            self.tasks['create'] = task.items()
        return self.tasks['create']

    def instantiate_vapp(self):
        task = self.vapp_object.instantiate_vapp()
        if 'create' in self.tasks:
            # Unlike returns from the SDK, this task is the list item returned
            # by vapp.instantiate_vapp
            self.tasks['create'].append(task[-1])
        else:
            self.tasks['create'] = [task[-1]]
        return self.tasks['create']

    def delete(self, vm_name=None):
        # TODO: This can be refactored:
        # To support bulk delete of VMs using vapp.delete_vms([names])
        vm = self.get_vm(vm_name or self.vm_name)
        task = vm.delete()
        self.tasks['delete'] = [task.items()]
        return self.tasks['delete']

    def power_on(self, vm_name=None):
        if not vm_name:
            self.vm.power_on()
        else:
            vm = self.get_vm(vm_name)
            vm.power_on()

    def power_off(self, vm_name=None):
        if not vm_name:
            self.vm.power_off()
        else:
            vm = self.get_vm(vm_name)
            vm.power_off()

    def shutdown(self, vm_name=None):
        if not vm_name:
            self.vm.shutdown()
        else:
            vm = self.get_vm(vm_name)
            vm.shutdown()

    def deploy(self, vm_name=None, power_on=True, force_customization=False):
        if not vm_name:
            self.vm.deploy(power_on, force_customization)
        else:
            vm = self.get_vm(vm_name)
            vm.deploy(power_on, force_customization)

    def undeploy(self, vm_name=None, action='default'):
        if not vm_name:
            self.vm.undeploy(action)
        else:
            vm = self.get_vm(vm_name)
            vm.undeploy(action)

    def attach_disk_to_vm(self, disk_href, vm_name=None):
        return self.vapp.attach_disk_to_vm(disk_href, vm_name or self.vm_name)

    def detach_disk_from_vm(self, disk_href, vm_name=None):
        return self.vapp.detach_disk_from_vm(
            disk_href, vm_name or self.vm_name)

    def add_nic(self, **kwargs):
        task = self.vm.add_nic(**kwargs)
        if 'add_nic' in self.tasks:
            self.tasks['add_nic'].append(task.items())
        else:
            self.tasks['add_nic'] = [task.items()]
        return self.tasks['add_nic']

    def delete_nic(self, index):
        task = self.vm.delete_nic(index)
        if 'remove_nic' in self.tasks:
            self.tasks['remove_nic'].append(task.items())
        else:
            self.tasks['remove_nic'] = [task.items()]
        return self.tasks['remove_nic']

    def update_nic(self, **kwargs):
        task = self.vm.update_nic(**kwargs)
        if 'update_nic' in self.tasks:
            self.tasks['update_nic'].append(task.items())
        else:
            self.tasks['update_nic'] = [task.items()]
        return self.tasks['update_nic']
