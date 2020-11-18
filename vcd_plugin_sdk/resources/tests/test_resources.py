import os
import mock
from io import BytesIO

from pyvcloud.vcd.vdc import VDC as pyvcloud_vdc
from pyvcloud.vcd.vapp import VApp as pyvcloud_vapp
from pyvcloud.vcd.client import Client as pyvcloud_client

from ..disk import (
    VCloudISO,
    VCloudDisk,
    VCloudMedia)
from ..base import VCloudResource

from ...connection import VCloudConnect
from ...tests import (TEST_CONFIG, TEST_CREDENTIALS)


@mock.patch('pyvcloud.vcd.vdc.VDC.get_vapp')
@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_resource(_, __, ___):
    logger = mock.Mock()
    tasks = mock.Mock()
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    resource = VCloudResource(vcloud_connect, 'vdc', 'vapp', tasks)
    assert isinstance(resource.client, pyvcloud_client)
    assert resource.tasks == tasks
    assert resource.connection == vcloud_connect
    assert isinstance(resource.vdc, pyvcloud_vdc)
    resource.task_successful(mock.Mock())
    assert resource.client.get_task_monitor.called
    assert isinstance(resource.vapp, pyvcloud_vapp)
    assert isinstance(resource.get_vapp('foo'), pyvcloud_vapp)
    assert resource.get_template('foo', 'bar') is not None


@mock.patch('pyvcloud.vcd.vdc.VDC.get_vapp')
@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_media(_, __, ___):
    logger = mock.Mock()
    tasks = mock.Mock()
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    config = {'catalog_name': 'foo', 'file_name': 'bar'}
    vcloud_media = VCloudMedia('foo', vcloud_connect, 'vdc', config, tasks)
    media_obj = mock.Mock()
    vcloud_media._media = media_obj
    E = {'href': 'foo/bar'}
    vcloud_media._media.Entity = E
    assert vcloud_media.name == 'foo.iso'
    assert vcloud_media.catalog_name == 'foo'
    assert vcloud_media.id == 'bar'
    assert vcloud_media.exposed_data == {
        'name': vcloud_media.name,
        'catalog_name': vcloud_media.catalog_name,
        'id': vcloud_media.id,
        'href': vcloud_media.href
    }
    assert vcloud_media.href == 'foo/bar'
    assert vcloud_media._entity == E
    assert vcloud_media.media == media_obj
    vcloud_media.get_media('foo', 'bar')
    assert vcloud_media.connection.org.get_catalog_item.called
    vcloud_media.upload()
    assert vcloud_media.connection.org.upload_media.called
    vcloud_media.delete()
    assert vcloud_media.connection.org.delete_catalog_item.called


def test_vcloud_iso():
    config = {
        'vol_ident': 'cidata',
        'sys_ident': '',
        'files': {'ISO/FOLDER/content.json': 'test content'}
    }
    iso = VCloudISO(config)
    path = iso.file
    assert os.path.exists(path)
    assert iso.file == path
    assert isinstance(iso.iso_material, BytesIO)
    assert iso.iso_material_size == 71680
    iso.delete()
    assert not os.path.exists(path)


@mock.patch('pyvcloud.vcd.vdc.VDC.get_disk')
@mock.patch('vcd_plugin_sdk.connection.Org', autospec=True)
@mock.patch('vcd_plugin_sdk.connection.Client', autospec=True)
def test_vcloud_disk(_, __, ___):
    logger = mock.Mock()
    tasks = {'create': [[{'id': 'bar'}, {'href': 'foo/bar'}]], 'delete': []}
    vcloud_connect = VCloudConnect(logger, TEST_CONFIG, TEST_CREDENTIALS)
    config = {'size': 2097152, 'description': 'test disk'}
    vcloud_disk = VCloudDisk('foo', vcloud_connect, 'vdc', config, tasks)
    assert vcloud_disk.name == 'foo'
    assert vcloud_disk.href == 'foo/bar'
    assert vcloud_disk._get_identifier('id') == 'bar'
    assert 'id', 'href' in vcloud_disk.exposed_data
    result = vcloud_disk.disk
    assert vcloud_disk.vdc.get_disk.called
    vcloud_disk.vdc.client.get_api_version = (lambda: '33')
    assert vcloud_disk.get_disk() == result
    vcloud_disk.create()
    vcloud_disk.delete()
