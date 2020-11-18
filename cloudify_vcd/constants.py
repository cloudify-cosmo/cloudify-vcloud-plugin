
from vcd_plugin_sdk.resources.vapp import VCloudvApp, VCloudVM
from vcd_plugin_sdk.resources.network import VCloudGateway, VCloudNetwork
from vcd_plugin_sdk.resources.disk import VCloudDisk, VCloudMedia, VCloudISO


class BsClass(object):
    def __init__(self, *_, **__):
        pass


TYPE_MATRIX = {
    'cloudify.nodes.vcloud.Gateway': [VCloudGateway],
    'cloudify.nodes.vcloud.NatRules': [BsClass, VCloudGateway],
    'cloudify.nodes.vcloud.FirewallRules': [BsClass, VCloudGateway],
    'cloudify.nodes.vcloud.DHCPPools': [BsClass, VCloudGateway],
    'cloudify.nodes.vcloud.StaticRoutes': [BsClass, VCloudGateway],
    'cloudify.nodes.vcloud.DirectlyConnectedVDCNetwork': [VCloudNetwork],
    'cloudify.nodes.vcloud.IsolatedVDCNetwork': [VCloudNetwork],
    'cloudify.nodes.vcloud.RoutedVDCNetwork': [VCloudNetwork],
    'cloudify.nodes.vcloud.VApp': [VCloudvApp],
    'cloudify.nodes.vcloud.VM': [VCloudVM, VCloudvApp],
    'cloudify.nodes.vcloud.Disk': [VCloudDisk, VCloudVM],
    'cloudify.nodes.vcloud.Media': [VCloudMedia, VCloudVM],
}

CLIENT_CONFIG_KEYS = ['uri', 'api_version', 'verify_ssl_certs', 'log_file',
                      'log_requests', 'log_headers', 'log_bodies']

CLIENT_CREDENTIALS_KEYS = ['user', 'password', 'org']

NO_RESOURCE_OK = ['unlink', 'delete', 'stop']
