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

import os
from tempfile import NamedTemporaryFile

from .base import VCloudResource
import cloudify_common_sdk.iso9660 as iso9660


class VCloudDisk(VCloudResource):

    def __init__(self,
                 disk_name,
                 connection=None,
                 vdc_name=None,
                 kwargs=None,
                 tasks=None):

        self._disk_name = disk_name
        self.kwargs = kwargs or {}
        self._disk = None
        if 'name' in self.kwargs:
            del self.kwargs['name']

        super().__init__(connection, vdc_name, tasks=tasks)
        self.vapp_name = self._vapp_name
        self._vapp = None
        self._id = None
        self._disk_href = None

    @property
    def name(self):
        return self._disk_name

    @property
    def href(self):
        if not self._disk_href:
            self._disk_href = self._get_identifier('href')
        return self._disk_href

    @property
    def id(self):
        if not self._id:
            self._id = self._get_identifier('id')
        return self._id

    def _get_identifier(self, identifier):
        if len(self.tasks['create']) > 0:
            for pair in self.tasks['create'][0]:
                if pair.get(identifier):
                    return pair.get(identifier)

    @property
    def disk(self):
        return self.get_disk()

    @property
    def exposed_data(self):
        return {
            'id': self.id,
            'href': self.href,
            'size': self.disk.get('size'),
            'status': self.disk.get('status'),
            'iops': self.disk.get('iops'),
            'busSubType': self.disk.get('busSubType'),
            'busType': self.disk.get('busType')
        }

    def get_disk(self, disk_id=None, disk_name=None):
        disk_id = disk_id or self.id
        if disk_id:
            return self.vdc.get_disk(disk_id=disk_id)
        else:
            return self.vdc.get_disk(disk_name or self.name)

    def create(self):
        task = self.vdc.create_disk(self.name, **self.kwargs)
        self.tasks['create'].append(task.items())
        self._disk_href = task.get('href')
        self._id = task.get('id')
        return task

    def delete(self, disk_id=None, disk_name=None):
        disk_id = disk_id or self.id
        if disk_id:
            task = self.vdc.delete_disk(disk_id=disk_id)
        else:
            task = self.vdc.delete_disk(disk_name or self.name)
        self.tasks['delete'].append(task.items())
        return task

    def update(self, disk_id=None, disk_name=None, **kwargs):
        disk_id = disk_id or self.id
        if disk_id:
            task = self.vdc.update_disk(disk_id=disk_id, **kwargs)
        else:
            task = self.vdc.update_disk(disk_name or self.name, **kwargs)
        self.tasks['update'].append(task.items())
        return task


class VCloudISO(object):

    def __init__(self, kwargs=None):

        self.kwargs = kwargs or {}
        self._iso_material = None
        self._iso_material_size = None
        self._file = None

    @property
    def file(self):
        if not self._file:
            self._file = self._create_file()
        return self._file

    @property
    def iso_material(self):
        if not self._iso_material:
            self.create_iso_material()
        self._iso_material.seek(0, os.SEEK_END)
        self._iso_material.seek(0, os.SEEK_END)
        return self._iso_material

    @property
    def iso_material_size(self):
        if not self._iso_material_size:
            if not self._iso_material:
                self.create_iso_material()
            self._iso_material.seek(0, os.SEEK_END)
            self._iso_material_size = self.iso_material.tell()
            self._iso_material.seek(0, os.SEEK_END)
        return self._iso_material_size

    @staticmethod
    def _create_iso_material(vol_ident, sys_ident, files):
        return iso9660.create_iso(vol_ident=vol_ident,
                                  sys_ident=sys_ident,
                                  files=files)

    def create_iso_material(self):
        self._iso_material = self._create_iso_material(
            self.kwargs.get('vol_ident'),
            self.kwargs.get('sys_ident'),
            self.kwargs.get('files'))

    def _create_file(self):
        f = NamedTemporaryFile(suffix='.iso', delete=False)
        f = f.name
        o = open(f, 'wb')
        o.write(self.iso_material.getbuffer())
        o.close()
        return f

    def delete(self):
        os.remove(self.file)


class VCloudMedia(VCloudResource):

    def __init__(self,
                 media_name,
                 connection=None,
                 vdc_name=None,
                 kwargs=None,
                 tasks=None):

        if not media_name.endswith('.iso'):
            media_name = media_name + '.iso'

        self._media_name = media_name
        self.kwargs = kwargs or {}
        self.kwargs['item_name'] = media_name
        self._disk = None
        super().__init__(connection, vdc_name, tasks=tasks)
        self._media = None
        self._exposed_data = {'name': self.name, 'catalog_name': self.catalog_name}

    @property
    def name(self):
        return self._media_name

    @property
    def id(self):
        return self.href.split('/')[-1]

    @property
    def exposed_data(self):
        if 'id' not in self._exposed_data:
            self._exposed_data['id'] = self.id
        if 'href' not in self._exposed_data:
            self._exposed_data['href'] = self.href
        return self._exposed_data

    @property
    def href(self):
        return self._entity.get('href')

    @property
    def _entity(self):
        return dict(self.media.Entity.items())

    @property
    def catalog_name(self):
        return self.kwargs.get('catalog_name')

    @property
    def media(self):
        if not self._media:
            self._media = self.connection.org.get_catalog_item(
            self.catalog_name, self.name)
        return self._media

    def get_media(self, catalog_name=None, media_name=None):
        catalog_name = catalog_name or self.catalog_name
        media_name = media_name or self.name
        return self.connection.org.get_catalog_item(catalog_name, media_name)

    def upload(self):
        self._exposed_data['bytes'] = self.connection.org.upload_media(**self.kwargs)

    def delete(self, catalog_name=None, media_name=None):
        catalog_name = catalog_name or self.catalog_name
        media_name = media_name or self.name
        self.connection.org.delete_catalog_item(catalog_name, media_name)
