import os
import urllib3
from datetime import datetime

from vcd_plugin_sdk.resources.disk import VCloudDisk, VCloudMedia, VCloudISO
from vcd_plugin_sdk.resources.vapp import VCloudvApp, VCloudVM
from vcd_plugin_sdk.resources.network import VCloudNetwork, VCloudGateway
from vcd_plugin_sdk.resources.storage_profile import VCloudStorageProfile
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

gateway = VCloudGateway('vCloud97-Edges', vdc_name='vCloud97')

rnow = datetime.now()
CREATE_ROUTED = {
    'network_cidr': '192.169.1.1/24',
    'gateway_name': 'vCloud97-Edges',
    'description': 'test routed network',
    'primary_dns_ip': '8.8.8.4',
    'secondary_dns_ip': '8.8.8.8',
    'ip_range_start': '192.169.1.2',
    'ip_range_end': '192.169.1.254'
}
routed_network_name = 'test-routed-network-{}'.format(rnow.strftime("%Y%m%d%H%M"))
routed_network = VCloudNetwork(
    routed_network_name,
    'routed_vdc_network',
    vdc_name='vCloud97',
    vapp_name='test',
    kwargs=CREATE_ROUTED
)

# Test Network Create
r2now = datetime.now()
CREATE_ROUTED2 = {
    'network_cidr': '192.169.2.1/24',
    'gateway_name': 'vCloud97-Edges',
    'description': 'test routed network',
    'primary_dns_ip': '8.8.8.4',
    'secondary_dns_ip': '8.8.8.8',
}
routed_network_name2 = 'test-routed-network2-{}'.format(r2now.strftime("%Y%m%d%H%M"))
routed_network2 = VCloudNetwork(
    routed_network_name2,
    'routed_vdc_network',
    vdc_name='vCloud97',
    vapp_name='test',
    kwargs=CREATE_ROUTED2
)

inow = datetime.now()
CREATE_ISOLATED = {
    'network_cidr': '192.169.3.1/24',
    'description': 'test isolated network',
    'primary_dns_ip': '8.8.8.4',
    'secondary_dns_ip': '8.8.8.8',
    # 'ip_range_start': '192.169.3.2',
    # 'ip_range_end': '192.169.3.254',
    'default_lease_time': 300,
    'max_lease_time': 900,
}
isolated_network = VCloudNetwork(
    'test-iso-network-{}'.format(inow.strftime("%Y%m%d%H%M")),
    'isolated_vdc_network',
    vdc_name='vCloud97',
    vapp_name='test',
    kwargs=CREATE_ISOLATED
)

CREATE_VAPP = {
    'description': 'test description',
    'network': routed_network.name,
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
    'network': routed_network.name,
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

ISO_CREATE_KWARGS = {
    'vol_ident': 'cidata',
    'sys_ident': '',
    'files': {
        'ISO/FOLDER/content.json': "test content"
    }
}
iso = VCloudISO(ISO_CREATE_KWARGS)

media_now = datetime.now()
MEDIA_CREATE_KWARGS = {
    'catalog_name': catalog_name,
    'file_name': iso.file,
}
media = VCloudMedia(
    os.path.basename(iso.file),
    vdc_name='vCloud97',
    kwargs=MEDIA_CREATE_KWARGS,
)


routed_network_create_result = routed_network.create()
routed_network2_create_result = routed_network2.create()
isolated_network_create_result = isolated_network.create()

# Test Static IPs
static_route = dict(network='192.169.3.0/24', next_hop='192.168.1.1')
static_route_create_result = gateway.add_static_route(**static_route)
gateway.delete_static_route(**static_route)


# Test Firewall Rule
test_rule_name = 'test-rule-{}'.format(rnow.strftime("%Y%m%d%H%M"))
firewall_rule_info = gateway.create_firewall_rule(test_rule_name, source_values=['VLAN-102' + ':gatewayinterface', routed_network.network.name + ':network', '192.169.1.0:ip'], destination_values=['VLAN-102' + ':gatewayinterface', routed_network.network.name + ':network', '192.169.1.0:ip'], services=[{'tcp': {'any': 'any'}}])
gateway.delete_firewall_rule(firewall_rule_info['Name'], firewall_rule_info['Id'])

# Test NAT rule
nat_rule = dict(action='dnat', original_address='10.10.4.2', translated_address='11.11.4.2', description='nat rule test value')
new_nat_rule = gateway.create_nat_rule(nat_rule)
gateway.delete_nat_rule(new_nat_rule['ID'])

# Test DHCP Pool
new_dhcp_rule = gateway.add_dhcp_pool(dict(ip_range='192.169.2.2-192.169.2.100'))
gateway.delete_dhcp_pool(dict(ip_range='192.169.2.2-192.169.2.100'))

# vapp.create()

vm_create_result = vm.instantiate_vapp()

add_network_result = vapp.add_network(orgvdc_network_name=routed_network2.name)
nic_create_result = vm.add_nic(adapter_type='VMXNET3', is_primary=False, is_connected=False, network_name=routed_network2.name, ip_address_mode='MANUAL', ip_address='192.169.2.2')
# vapp.add_network(orgvdc_network_name=isolated_network.network.name)
# vm.add_nic(adapter_type='VMXNET3', is_primary=False, is_connected=False, network_name=isolated_network.network.name, ip_address_mode='MANUAL', ip_address='192.169.3.2')

disk_create_result = disk.create()
upload_media_result = media.upload()

attach_disk_result = vm.attach_disk_to_vm(disk.href)
attach_media_result = vm.attach_media(media.href)

vapp.deploy()
delete_network_result = vapp.remove_network(routed_network2.name)

vm.eject_media(media.name)
vm.detach_disk_from_vm(disk.href)
media.delete()
iso.delete()
vm.delete_nic()
vapp.undeploy()
vapp.delete()


isolated_network.delete()
routed_network2.delete()
routed_network.delete()
