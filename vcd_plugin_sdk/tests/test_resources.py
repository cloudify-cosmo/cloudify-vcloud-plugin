import urllib3
from datetime import datetime

from vcd_plugin_sdk.resources.disk import VCloudDisk
from vcd_plugin_sdk.resources.vapp import VCloudvApp, VCloudVM
from vcd_plugin_sdk.resources.network import VCloudNetwork, VCloudGateway
from vcd_plugin_sdk.resources.storage_profile import VCloudStorageProfile
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

gateway = VCloudGateway('vCloud97-Edge', vdc_name='vCloud97')

# Test Network Create
now = datetime.now()
CREATE_ROUTED2 = {
    'network_cidr': '192.169.2.1/24',
    'gateway_name': 'vCloud97-Edge',
    'description': 'test routed network',
    'primary_dns_ip': '8.8.8.4',
    'secondary_dns_ip': '8.8.8.8',
}
routed_network_name2 = 'test-routed-network-{}'.format(now.strftime("%Y%m%d%H%M"))
routed_network2 = VCloudNetwork(
    routed_network_name2,
    'routed_vdc_network',
    vdc_name='vCloud97',
    vapp_name='test',
    kwargs=CREATE_ROUTED2
)
routed_network2_create_result = routed_network2.create()

now = datetime.now()
test_rule_name = 'test-rule-{}'.format(now.strftime("%Y%m%d%H%M"))

# Test Firewall Rule
firewall_rule_info = gateway.create_firewall_rule(test_rule_name, source_values=['VLAN-102' + ':gatewayinterface', routed_network.network.name + ':network', '192.169.1.0:ip'], destination_values=['VLAN-102' + ':gatewayinterface', routed_network.network.name + ':network', '192.169.1.0:ip'], services=[{'tcp': {'any': 'any'}}])
gateway.delete_firewall_rule(firewall_rule_info['Name'], firewall_rule_info['Id'])

# Test NAT rule
new_nat_rule = gateway.create_nat_rule()
gateway.delete_nat_rule(new_nat_rule['ID'])

# Test DHCP Pool
new_dhcp_rule = gateway.add_dhcp_pool(ip_range='192.169.2.2-192.169.2.100')
gateway.delete_dhcp_pool(ip_range='192.169.2.2-192.169.2.100')

# Test Static IPs
static_route = dict(network='192.169.1.0/24', next_hop='192.168.1.1')
gateway.add_static_route(**static_route)
gateway.delete_static_route(**static_route)


now = datetime.now()
CREATE_ROUTED = {
    'network_cidr': '192.169.1.1/24',
    'gateway_name': 'vCloud97-Edge',
    'description': 'test routed network',
    'primary_dns_ip': '8.8.8.4',
    'secondary_dns_ip': '8.8.8.8',
    'ip_range_start': '192.169.1.2',
    'ip_range_end': '192.169.1.254'
}
routed_network_name = 'test-routed-network-{}'.format(now.strftime("%Y%m%d%H%M"))
routed_network = VCloudNetwork(
    routed_network_name,
    'routed_vdc_network',
    vdc_name='vCloud97',
    vapp_name='test',
    kwargs=CREATE_ROUTED
)
routed_network_create_result = routed_network.create()

now = datetime.now()
CREATE_ISOLATED = {
    'network_cidr': '192.169.3.1/24',
    'description': 'test isolated network',
    'primary_dns_ip': '8.8.8.4',
    'secondary_dns_ip': '8.8.8.8',
    'ip_range_start': '192.169.3.2',
    'ip_range_end': '192.169.3.254',
    'default_lease_time': 300,
    'max_lease_time': 900,
}
isolated_network = VCloudNetwork(
    'test-iso-network-{}'.format(now.strftime("%Y%m%d%H%M")),
    'isolated_vdc_network',
    vdc_name='vCloud97',
    vapp_name='test',
    kwargs=CREATE_ISOLATED
)

isolated_network_create_result = isolated_network.create()

CREATE_VAPP = {
    'description': 'test description',
    'network': routed_network.network.name,
    'fence_mode': 'natRouted',
    'accept_all_eulas': True
}
vapp_now = datetime.now()
vapp_name = 'test-vapp-{}'.format(vapp_now.strftime("%Y%m%d%H%M"))
vapp = VCloudvApp(
    vapp_name,
    vdc_name='vCloud97',
    kwargs=CREATE_VAPP
)
catalog_name = 'testcatalogue'
template = vapp.get_template('testcatalogue', 'Centos7-GenericCloud')

INSTANTIATE_VAPP = {
    'name': 'test-vm-{}'.format(vapp_now.strftime("%Y%m%d%H%M")),
    'catalog': catalog_name,
    'template': template.get('name'),
    'description': 'test description',
    'network': routed_network.network.name,
    'fence_mode': 'bridged',
    'ip_allocation_mode': 'manual',
    'deploy': False,
    'power_on': False,
    'accept_all_eulas': True,
    # 'memory': 2048,
    # 'cpu': 1,
    # 'disk_size': 77824,
    'password': 'test_password',
    'vm_name': 'test-vm-{}'.format(vapp_now.strftime("%Y%m%d%H%M")),
    'hostname': 'test-vm-{}'.format(vapp_now.strftime("%Y%m%d%H%M")),
    'ip_address': '192.169.1.2',
}

vm_now = datetime.now()
vm = VCloudVM(
    'test-vm-{}'.format(vapp_now.strftime("%Y%m%d%H%M")),
    vdc_name='vCloud97',
    vapp_name=vapp_name,
    kwargs={},
    vapp_kwargs=INSTANTIATE_VAPP)
vm_create_result = vm.instantiate_vapp()

vapp.add_network(orgvdc_network_name=routed_network2.network.name)

vm.add_nic(adapter_type='VMXNET3', is_primary=False, is_connected=False, network_name=routed_network2.network.name, ip_address_mode='MANUAL', ip_address='192.169.2.2')

vapp.add_network(orgvdc_network_name=isolated_network.network.name)

vm.add_nic(adapter_type='VMXNET3', is_primary=False, is_connected=False, network_name=isolated_network.network.name, ip_address_mode='MANUAL', ip_address='192.169.3.2')

vm.power_on()

vm.power_off()
vm.vm.is_powered_off()
vm.undeploy()
vm.delete()

CREATE_DISK = {
    'size': 2097152,
    'description': 'test disk'
}
disk_now = datetime.now()
disk_name = 'test-disk-{}'.format(disk_now.strftime("%Y%m%d%H%M"))
disk = VCloudDisk(
    disk_name,
    vdc_name='vCloud97',
    kwargs=CREATE_DISK
)
disk_create_result = disk.create()
vm.attach_disk_to_vm(disk.href)
    vm.detach_disk_from_vm(disk.href)


# vapp_create_result = vapp.create()

# CREATE_VM = {
#     # 'specs': {
#     #     'vm_name': 'test-vm-{}'.format(vapp_now.strftime("%Y%m%d%H%M")),
#     #     'comp_name': 'test-vm-{}'.format(vapp_now.strftime("%Y%m%d%H%M"))[0:15],
#     #     'description': 'test description',
#     #     'os_type': 'linux',
#     #     'media_href': catalogue_item.Entity.get('href'),
#     #     'media_name': catalogue_item.Entity.get('name'),
#     #     'media_id': catalogue_item.Entity.get('id')
#     # },
#     'specs': [
#         {
#             'vapp': catalogue_item.Entity.get('href'),
#             'source_vm_name': '',
#             'target_vm_name': 'test-vm-{}'.format(vapp_now.strftime("%Y%m%d%H%M")),
#             'hostname': 'test-vm-{}'.format(vapp_now.strftime("%Y%m%d%H%M"))[0:15],
#             # 'network': routed_network.network.name,
#         }
#     ],
#     'all_eulas_accepted': True,
#     'power_on': False,
#     'deploy': False,
# }
# CREATE_DIRECT = {
#     'parent_network_name': routed_network.network.name,
#     'description': 'test directly connected network'
#
# }
# directly_connected_network = VCloudNetwork(
#     'test-direct-network-{}'.format(now.strftime("%d-%m-%Y-%H-%M")),
#     'directly_connected_vdc_network',
#     vdc_name='vCloud97',
#     vapp_name='test',
#     kwargs=CREATE_DIRECT
# )
# directly_connected_network_create_result = directly_connected_network.create()
# directly_connected_network_delete_result = directly_connected_network.delete()


# vapp.connection.org.list_catalog_items('testcatalogue')
# catalogue_item.Entity.get('href')
# catalogue_item.Entity.get('id')

# # Test Network Create