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
import sys
import logging

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.client import Client, BasicLoginCredentials


# def default_logger(stream=sys.stdout):
def default_logger(stream=sys.stdout):

    logging.basicConfig(
        # stream=stream,
        # filename=os.path.join(
        #     os.path.expanduser('~'),
        #     'Desktop', 'vcloudclient.log'),
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%y.%m.%d-%H:%M:%S')
    return logging.getLogger(__name__)


class VCloudDataBase(object):

    kwargs = None
    logger = None
    _valid_dict = None

    def _validate(self):
        """Check what the user sent and warn if there is some irregularity."""
        if self.kwargs:
            self.logger.warn(
                'vcloud_sdk.client.VCloudClientConfiguration '
                'received invalid parameters. Invalid: [{invalid}]. '
                'Supported keys are [{supported}].'.format(
                    invalid=self.kwargs,
                    supported=self._valid_dict()))


class VCloudCredentials(VCloudDataBase):

    def __init__(self,
                 logger,
                 user,
                 password,
                 org,
                 **kwargs):

        self.logger = logger

        self.username = user
        self.password = password
        self.org = org
        self.kwargs = kwargs
        self._validate()

    def _valid_dict(self):
        return {
            'user': self.username,
            'password': self.password,
            'org': self.org
        }

    def asdict(self):
        credentials_dict = self._valid_dict()
        credentials_dict.update(**self.kwargs)
        return credentials_dict


class VCloudClientConfiguration(object):

    def __init__(self,
                 logger,
                 uri,
                 api_version=None,
                 verify_ssl_certs=True,
                 log_file=None,
                 log_requests=True,
                 log_headers=False,
                 log_bodies=False,
                 **kwargs):
        """Class that represents the dictionary of kwargs sent to
        pyvcloud.vcd.client.Client.

        :param uri:
        :param api_version:
        :param verify_ssl_certs:
        :param log_file:
        :param log_requests:
        :param log_headers:
        :param log_bodies:
        :param kwargs:
        """

        self.logger = logger

        self.uri = uri
        self.api_version = api_version or '32.0'
        self.verify_ssl_certs = verify_ssl_certs
        self.log_file = log_file
        self.log_requests = log_requests
        self.log_headers = log_headers
        self.log_bodies = log_bodies
        self.kwargs = kwargs
        self._validate()

    def _validate(self):
        """Check what the user sent and warn if there is some irregularity."""
        if self.kwargs:
            self.logger.warn(
                'vcloud_sdk.client.VCloudClientConfiguration '
                'received invalid parameters. Invalid: [{invalid}]. '
                'Supported keys are [{supported}].'.format(
                    invalid=self.kwargs,
                    supported=self._valid_dict()))

    def _valid_dict(self):
        return {
            'uri': self.uri,
            'api_version': self.api_version,
            'verify_ssl_certs': self.verify_ssl_certs,
            'log_file': self.log_file,
            'log_requests': self.log_requests,
            'log_headers': self.log_headers,
            'log_bodies': self.log_bodies
        }

    def asdict(self):
        client_configuration = self._valid_dict()
        client_configuration.update(**self.kwargs)
        return client_configuration


class VCloudConnect(object):

    def __init__(self, logger=None, client_config=None, credentials=None):

        client_config = client_config or \
            self.get_client_config_from_environment()
        credentials = credentials or self.get_credentials_from_environment()

        self.logger = logger or default_logger(client_config.get('log_file'))

        self.client_config = VCloudClientConfiguration(
            logger=self.logger, **client_config)
        self.credentials = VCloudCredentials(
            logger=self.logger, **credentials)

    @property
    def client(self):
        client = Client(**self.client_config.asdict())
        client.set_credentials(
            BasicLoginCredentials(**self.credentials.asdict()))
        return client

    @staticmethod
    def get_client_config_from_environment():
        return {
            'uri': os.environ.get('VCLOUD_HOST', ''),
            'api_version': os.environ.get('VCLOUD_API_VERSION'),
            'verify_ssl_certs': os.environ.get('VCLOUD_SSL_VERIFY', False),
            'log_file': os.environ.get(
                'VCLOUD_LOG_FILE',
                os.path.join(os.path.expanduser('~'), 'pyvcloud.log')),
        }

    @staticmethod
    def get_credentials_from_environment():
        return {
            'user': os.environ.get('VCLOUD_USER', ''),
            'password': os.environ.get('VCLOUD_PASS', ''),
            'org': os.environ.get('VCLOUD_ORG', '')
        }

    @property
    def org(self):
        return self.get_org()

    def get_org(self, org_name=None):
        if org_name:
            logged_in_org = self.client.get_org_by_name(org_name)
        else:
            logged_in_org = self.client.get_org()
        return Org(self.client, resource=logged_in_org)
