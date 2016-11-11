# Copyright (c) 2016 CompuNova Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from oslo_config import cfg
from haikunator import Haikunator
from nova.compute import power_state
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.common.credentials import ServicePrincipalCredentials
from azure.servicemanagement import ServiceManagementService
from msrestazure.azure_exceptions import CloudError, CloudErrorData

from ..common import BaseProvider


haikunator = Haikunator()

VM_REFERENCE = {
    'UbuntuServer': {
        'publisher': 'Canonical',
        'offer': 'UbuntuServer',
        'sku': '16.04.0-LTS',
        'version': 'latest'
    },
    'windows': {
        'publisher': 'MicrosoftWindowsServerEssentials',
        'offer': 'WindowsServerEssentials',
        'sku': 'WindowsServerEssentials',
        'version': 'latest'
    }
}

POWER_STATE_MAP = {
    'PowerState/running': power_state.RUNNING,
    'PowerState/starting': power_state.NOSTATE,
    'PowerState/deallocating': power_state.NOSTATE,
    'PowerState/deallocated': power_state.SHUTDOWN,
    'PowerState/stopped': power_state.SHUTDOWN,
    'PowerState/stopping': power_state.NOSTATE,
    # power_state.PAUSED,
    # power_state.CRASHED,
    # power_state.STATE_MAP,
    # power_state.SUSPENDED,
}


class AzureProvider(BaseProvider):

    def __init__(self):
        super(AzureProvider, self).__init__()
        self.name = 'AZURE'
        self.config_name = 'kozinaki_' + self.name

    @staticmethod
    def get_management_service(service, config):
        if service is ServiceManagementService:
            return ServiceManagementService(config['subscription_id'], config['key_file'])
        else:
            credential_service = ServicePrincipalCredentials(
                client_id=config['app_client_id'],
                secret=config['app_secret'],
                tenant=config['app_tenant']
            )
            return service(credentials=credential_service, subscription_id=config['subscription_id'])

    def get_credentials(self):
        config = self.load_config()
        credential_service = ServicePrincipalCredentials(
            client_id=config['app_client_id'],
            secret=config['app_secret'],
            tenant=config['app_tenant']
        )
        return credential_service, config['subscription_id']

    def load_config(self):
        """Load config options from nova config file or command line (for example: /etc/nova/nova.conf)

        Sample settings in nova config:
            [kozinaki_EC2]
            user=AKIAJR7NAEIZPWSTFBEQ
            key=zv9zSem8OE+k/axFkPCgZ3z3tLrhvFBaIIa0Ik0j
        """

        provider_opts = [
            cfg.StrOpt('subscription_id', help='Subscribe is from azure portal settings'),
            cfg.StrOpt('key_file', help='API key to work with the cloud provider', secret=True),
            cfg.StrOpt('username', help='Default vm username'),
            cfg.StrOpt('password', help='Azure: default instance password. '
                                        'Password must be 6-72 characters long'),
            cfg.StrOpt('app_client_id', help='Azure app client id'),
            cfg.StrOpt('app_secret', help='Azure app secret'),
            cfg.StrOpt('app_tenant', help='Azure app tenant'),
            cfg.StrOpt('resource_group_name', help='Azure resource group name'),
            cfg.StrOpt('location', help='VM location'),
            cfg.StrOpt('storage_account_name', help='Azure storage account name'),
            cfg.StrOpt('os_disk_name', help='VM default disk name'),
            cfg.StrOpt('vnet_name', help='Azure default virtual network'),
            cfg.StrOpt('subnet_name', help='Azure default subnet name'),
            cfg.StrOpt('ip_config_name', help='Azure default ip config name'),
            cfg.StrOpt('nic_name', help='Azure default nic name'),
        ]

        cfg.CONF.register_opts(provider_opts, self.config_name)
        return cfg.CONF[self.config_name]

    def list_nodes(self):
        config = self.load_config()
        compute_client = self.get_management_service(ComputeManagementClient, config=config)
        return list(compute_client.virtual_machines.list_all())

    def list_sizes(self):
        config = self.load_config()
        sms = self.get_management_service(StorageManagementClient, config=config)
        return list(sms.list_role_sizes())

    def create_node(self, instance, image_meta, *args, **kwargs):
        config = self.load_config()

        # Get info
        image_id = getattr(image_meta.properties, 'os_distro')
        node_name = instance.uuid
        flavor_name = instance.flavor['name']

        # Get services
        resource_client = self.get_management_service(ResourceManagementClient, config=config)
        compute_client = self.get_management_service(ComputeManagementClient, config=config)

        # Get or create resource group
        resource_group = resource_client.resource_groups.create_or_update(
            config['resource_group_name'],
            {'location': config['location']}
        )

        # Configure network
        network = self._get_or_create_vnet(config=config)
        subnet_info = self._get_or_create_subnet(config=config)
        nic = self._get_or_create_nic(subnet_info=subnet_info, config=config)

        vm_parameters = self._create_vm_parameters(
            vm_name=node_name,
            vm_size=flavor_name,
            nic_id=nic.id,
            vm_reference=VM_REFERENCE[image_id],
            config=config
        )

        async_vm_creation = compute_client.virtual_machines.create_or_update(
            config['resource_group_name'],
            node_name,
            vm_parameters
        )

    def _create_vm_parameters(self, vm_name, vm_size, nic_id, vm_reference, config=None):
        """Create the VM parameters structure"""
        config = config or self.load_config()
        return {
            'location': config['location'],
            'os_profile': {
                'computer_name': vm_name,
                'admin_username': config['username'],
                'admin_password': config['password']
            },
            'hardware_profile': {
                'vm_size': vm_size
            },
            'storage_profile': {
                'image_reference': {
                    'publisher': vm_reference['publisher'],
                    'offer': vm_reference['offer'],
                    'sku': vm_reference['sku'],
                    'version': vm_reference['version']
                },
                'os_disk': {
                    'name': config['os_disk_name'],
                    'caching': 'None',
                    'create_option': 'fromImage',
                    'vhd': {
                        'uri': 'https://{}.blob.core.windows.net/vhds/{}.vhd'.format(
                            config['storage_account_name'], vm_name + haikunator.haikunate())
                    }
                },
            },
            'network_profile': {
                'network_interfaces': [{
                    'id': nic_id,
                }]
            },
        }

    def _get_or_create_nic(self, subnet_info, config=None):
        config = config or self.load_config()

        network_client = self.get_management_service(NetworkManagementClient, config=config)

        for nic in network_client.network_interfaces.list_all():
            if not nic.virtual_machine:
                return nic
        else:

            # Create new one
            async_nic_creation = network_client.network_interfaces.create_or_update(
                config['resource_group_name'],
                config['nic_name'] + haikunator.haikunate(),
                {
                    'location': config['location'],
                    'ip_configurations': [{
                        'name': config['ip_config_name'],
                        'subnet': {
                            'id': subnet_info.id
                        }
                    }]
                }
            )
            return async_nic_creation.result()

    def _get_or_create_subnet(self, config=None):
        config = config or self.load_config()

        network_client = self.get_management_service(NetworkManagementClient, config=config)

        # Try get existing storage by name
        try:
            return network_client.subnets.get(config['resource_group_name'], config['vnet_name'], config['subnet_name'])
        except CloudError, error:
            if not isinstance(error.inner_exception, CloudErrorData) or \
                            error.inner_exception.error != 'ResourceNotFound':
                raise error

        # Create new one
        async_subnet_creation = network_client.subnets.create_or_update(
            config['resource_group_name'],
            config['vnet_name'],
            config['subnet_name'],
            {'address_prefix': '10.0.1.0/24'}
        )
        async_subnet_creation.wait()
        return async_subnet_creation.result()

    def _get_or_create_vnet(self, config=None):
        config = config or self.load_config()

        network_client = self.get_management_service(NetworkManagementClient, config=config)

        # Try get existing storage by name
        try:
            return network_client.virtual_networks.get(config['resource_group_name'], config['vnet_name'])
        except CloudError, error:
            if not isinstance(error.inner_exception, CloudErrorData) or \
                              error.inner_exception.error != 'ResourceNotFound':
                raise error

        # Create new one
        async_vnet_creation = network_client.virtual_networks.create_or_update(
            config['resource_group_name'],
            config['vnet_name'],
            {
                'location': config['location'],
                'address_space': {
                    'address_prefixes': ['10.0.0.0/16']
                }
            }
        )
        async_vnet_creation.wait()
        return async_vnet_creation.result()

    def get_or_create_storage_account(self, config=None):
        config = config or self.load_config()

        storage_client = self.get_management_service(StorageManagementClient, config)

        # Find existing storage account
        try:
            return storage_client.storage_accounts.get_properties(config['resource_group_name'],
                                                                  config['storage_account_name'])
        except CloudError, error:
            if not isinstance(error.inner_exception, CloudErrorData) or \
                              error.inner_exception.error != 'ResourceNotFound':
                raise error

        # Create new account
        storage_async_operation = storage_client.storage_accounts.create(
            config['resource_group_name'],
            config['storage_account_name'],
            {
                'sku': {'name': 'standard_lrs'},
                'kind': 'storage',
                'location': config['location']
            }
        )
        storage_async_operation.wait()
        return storage_async_operation.result()

    def _get_node_by_name(self, node_name):
        """Get node instance by name

        We need to use expand param to get full instance info from InstanceView (e.g. power state).
        More details in this issue: https://github.com/Azure/azure-rest-api-specs/issues/117
        """
        config = self.load_config()

        compute_client = self.get_management_service(ComputeManagementClient, config=config)

        try:
            return compute_client.virtual_machines.get(config['resource_group_name'], node_name, expand='InstanceView')
        except CloudError, error:
            if not isinstance(error.inner_exception, CloudErrorData) or \
                              error.inner_exception.error != 'ResourceNotFound' or 'not found' not in error.message:
                raise error

    def destroy(self, instance, *args, **kwargs):
        config = self.load_config()
        compute_client = self.get_management_service(ComputeManagementClient, config=config)

        compute_client.virtual_machines.delete(config['resource_group_name'], instance.uuid)

    def reboot(self, instance, *args, **kwargs):
        config = self.load_config()
        compute_client = self.get_management_service(ComputeManagementClient, config=config)

        compute_client.virtual_machines.restart(config['resource_group_name'], instance.uuid)

    def power_off(self, instance, timeout=0, retry_interval=0):
        config = self.load_config()
        compute_client = self.get_management_service(ComputeManagementClient, config=config)

        compute_client.virtual_machines.power_off(config['resource_group_name'], instance.uuid)

    def power_on(self, context, instance, network_info, block_device_info=None):
        config = self.load_config()
        compute_client = self.get_management_service(ComputeManagementClient, config=config)

        compute_client.virtual_machines.start(config['resource_group_name'], instance.uuid)

    def get_info(self, instance):
        node = self._get_node_by_name(instance.uuid)

        if node:

            node_id = node.vm_id
            if len(node.instance_view.statuses) == 2:
                node_provision_state, node_power_state = node.instance_view.statuses
                node_state = POWER_STATE_MAP[node_power_state.code]
            else:
                node_state = power_state.NOSTATE

        else:
            node_state = power_state.NOSTATE
            node_id = 0

        node_info = {
            'state':          node_state,
            'max_mem_kb':     0, # '(int) the maximum memory in KBytes allowed',
            'mem_kb':         0, # '(int) the memory in KBytes used by the instance',
            'num_cpu':        0, # '(int) the number of virtual CPUs for the instance',
            'cpu_time_ns':    0, # '(int) the CPU time used in nanoseconds',
            'id':             node_id
        }

        return node_info

    def list_instances(self):
        return [node.name for node in self.list_nodes()]

    def list_instance_uuids(self):
        return [node.uuid for node in self.list_nodes()]
