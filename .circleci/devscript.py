import os
import urllib3
from time import sleep
from datetime import datetime

from vcd_plugin_sdk.resources.disk import VCloudDisk, VCloudMedia, VCloudISO
from vcd_plugin_sdk.resources.vapp import VCloudvApp, VCloudVM
from vcd_plugin_sdk.resources.network import VCloudNetwork, VCloudGateway
# from vcd_plugin_sdk.resources.storage_profile import VCloudStorageProfile
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


NOW = datetime.now().strftime("%Y%m%d%H%M")
NETWORK_NAME = 'test-routed-network-{}'.format(NOW)
GATEWAY_NAME = os.environ['VCLOUD_GATEWAY']
VCD_NAME = os.environ['VCLOUD_ORG']


def get_gateway():
    # static_route = dict(network='192.169.3.0/24', next_hop='192.168.1.1')
    # static_route_create_result = gateway.add_static_route(**static_route)
    # gateway.delete_static_route(**static_route)
    #
    #
    # # Test Firewall Rule
    # test_rule_name = 'test-rule-{}'.format(rnow.strftime("%Y%m%d%H%M"))
    # firewall_rule_info = gateway.create_firewall_rule(test_rule_name,
    # source_values=['VLAN-102' + ':gatewayinterface',
    # routed_network.network.name + ':network', '192.169.1.0:ip'],
    # destination_values=['VLAN-102' + ':gatewayinterface',
    # routed_network.network.name + ':network', '192.169.1.0:ip'], services=[
    # {'tcp': {'any': 'any'}}])
    # gateway.delete_firewall_rule(firewall_rule_info['Name'],
    # firewall_rule_info['Id'])
    #
    # # Test NAT rule
    # nat_rule = dict(action='dnat', original_address='10.10.4.2',
    # translated_address='11.11.4.2', description='nat rule test value')
    # new_nat_rule = gateway.create_nat_rule(nat_rule)
    # gateway.delete_nat_rule(new_nat_rule['ID'])
    #
    # # Test DHCP Pool
    # new_dhcp_rule = gateway.add_dhcp_pool(dict(
    # ip_range='192.169.2.2-192.169.2.100'))
    # gateway.delete_dhcp_pool(dict(ip_range='192.169.2.2-192.169.2.100'))
    return VCloudGateway(NETWORK_NAME, vdc_name=VCD_NAME)


def get_routed_network():
    create_routed = {
        'network_cidr': '192.169.169.1/24',
        'gateway_name': GATEWAY_NAME,
        'description': 'test routed network',
        'primary_dns_ip': '8.8.8.4',
        'secondary_dns_ip': '8.8.8.8',
        'ip_range_start': '192.169.169.2',
        'ip_range_end': '192.169.169.254'
    }
    network = VCloudNetwork(
        NETWORK_NAME,
        'routed_vdc_network',
        vdc_name=VCD_NAME,
        vapp_name='test',
        kwargs=create_routed
    )
    network.create()
    return network


def get_isolated_network():
    create_isolated = {
        'network_cidr': '192.169.3.1/24',
        'description': 'test isolated network',
        'primary_dns_ip': '8.8.8.4',
        'secondary_dns_ip': '8.8.8.8',
        'default_lease_time': 300,
        'max_lease_time': 900,
    }
    isolated_network = VCloudNetwork(
        'test-iso-network-{}'.format(NOW),
        'isolated_vdc_network',
        vdc_name=VCD_NAME,
        vapp_name='test',
        kwargs=create_isolated
    )
    isolated_network.create()
    return isolated_network


def get_vapp(network_name):

    create_vapp = {
        'description': 'test description',
        'network': network_name,
        'fence_mode': 'natRouted',
        'accept_all_eulas': True
    }
    vapp_name = 'test-vapp-{}'.format(NOW)
    vapp = VCloudvApp(
        vapp_name,
        vdc_name=VCD_NAME,
        kwargs=create_vapp
    )
    catalog_name = 'testcatalogue'
    template = vapp.get_template('testcatalogue', 'Centos7-GenericCloud')

    instantiate_vapp = {
        'name': 'test-vm-{}'.format(NOW),
        'catalog': catalog_name,
        'template': template.get('name'),
        'description': 'test description',
        'network': routed_network.name,
        'fence_mode': 'bridged',
        'ip_allocation_mode': 'manual',
        'deploy': False,
        'power_on': False,
        'accept_all_eulas': True,
        'password': 'test_password',
        'vm_name': 'test-vm-{}'.format(NOW),
        'hostname': 'test-vm-{}'.format(NOW),
        'ip_address': '192.169.169.2',
    }
    vm = VCloudVM(
        'test-vm-{}'.format(NOW),
        vdc_name=VCD_NAME,
        vapp_name=vapp_name,
        kwargs={},
        vapp_kwargs=instantiate_vapp)
    vm.instantiate_vapp()
    sleep(60)
    vapp.deploy()
    # To add network: add_network_result = vapp.add_network(
    # orgvdc_network_name=routed_network2.name)
    # To remove network: delete_network_result = vapp.remove_network(
    # routed_network2.name)
    return vapp


def get_disk():
    create_disk = {
        'size': 2097152,
        'description': 'test disk'
    }
    disk_now = datetime.now()
    disk_name = 'test-disk-{}'.format(disk_now.strftime("%Y%m%d%H%M"))
    disk = VCloudDisk(
        disk_name,
        vdc_name='vCloud97',
        kwargs=create_disk
    )
    disk.create()
    # To attach: attach_disk_result = vm.attach_disk_to_vm(disk.href)
    # To detach: vm.detach_disk_from_vm(disk.href)
    return disk


def get_media(catalog_name):
    # To get catalog_name, check get_vapp.
    create_iso = {
        'vol_ident': 'cidata',
        'sys_ident': '',
        'files': {
            'ISO/FOLDER/content.json': "test content"
        }
    }
    iso = VCloudISO(create_iso)
    media_create = {
        'catalog_name': catalog_name,
        'file_name': iso.file,
    }
    media = VCloudMedia(
        os.path.basename(iso.file),
        vdc_name='vCloud97',
        kwargs=media_create,
    )
    media.upload()
    # To delete execute media.delete() iso.delete()
    # To attach: attach_media_result = vm.attach_media(media.href)
    # To detaych: vm.eject_media(media.name)
    return media


if __name__ == '__main__':
    print('**step 1**')
    gateway = get_gateway()
    print('**step 2**')
    routed_network = get_routed_network()
    print('**step 3**')
    isolated_network = get_isolated_network()
    print('**step 4**')
    vapp = get_vapp(routed_network.name)

    sleep(60)

    print('**step 5**')
    vapp.undeploy()
    sleep(20)
    print('**step 6**')
    vapp.delete()
    print('**step 7**')
    isolated_network.delete()
    print('**step 8**')
    routed_network.delete()
