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
import boto3
from oslo_config import cfg
from haikunator import Haikunator
from nova.compute import power_state

from ..common import BaseProvider


haikunator = Haikunator()


POWER_STATE_MAP = {
    0:  power_state.NOSTATE,
    16: power_state.RUNNING,
    32: power_state.NOSTATE,
    48: power_state.SHUTDOWN,
    64: power_state.NOSTATE,
    80: power_state.SHUTDOWN,
    # power_state.PAUSED,
    # power_state.CRASHED,
    # power_state.STATE_MAP,
    # power_state.SUSPENDED,
}


class AWSProvider(BaseProvider):

    def __init__(self):
        super(AWSProvider, self).__init__()
        self.name = 'AWS'
        self.config_name = 'kozinaki_' + self.name
        self.driver = self.get_driver()

    def get_driver(self):
        config = self.load_config()

        session = boto3.session.Session(
            aws_access_key_id=config['aws_access_key_id'],
            aws_secret_access_key=config['aws_secret_access_key'],
            region_name=config['region']
        )
        return session.resource('ec2')

    def load_config(self):
        """Load config options from nova config file or command line (for example: /etc/nova/nova.conf)

        Sample settings in nova config:
            [kozinaki_EC2]
            user=AKIAJR7NAEIZPWSTFBEQ
            key=zv9zSem8OE+k/axFkPCgZ3z3tLrhvFBaIIa0Ik0j
        """

        provider_opts = [
            cfg.StrOpt('aws_secret_access_key', help='AWS secret key', secret=True),
            cfg.StrOpt('aws_access_key_id', help='AWS access key id', secret=True),
            cfg.StrOpt('region', help='AWS region name'),
        ]

        cfg.CONF.register_opts(provider_opts, self.config_name)
        return cfg.CONF[self.config_name]

    def create_node(self, instance, image_meta, *args, **kwargs):
        config = self.load_config()

        # Get info
        image_id = getattr(image_meta.properties, 'os_distro')
        flavor_name = instance.flavor['name']

        aws_instance = self.driver.create_instances(ImageId=image_id, InstanceType=flavor_name,
                                                    MinCount=1, MaxCount=1)[0]

        # Add openstack image uuid to tag
        aws_instance.create_tags(Tags=[{'Key': 'openstack_server_id', 'Value': instance.uuid}])
        return aws_instance

    def list_nodes(self):
        return list(self.driver.instances.all())

    def destroy(self, instance, *args, **kwargs):
        aws_node = self._get_node_by_uuid(instance.uuid)
        if aws_node:
            aws_node.terminate()

    def list_instances(self):
        return list(self.driver.instances.all())

    def list_sizes(self):
        return list(self.driver.images.all())

    def power_on(self, context, instance, network_info, block_device_info=None):
        aws_node = self._get_node_by_uuid(instance.uuid)
        if aws_node:
            aws_node.start()

    def list_instance_uuids(self):
        return [node.id for node in self.list_nodes()]

    def power_off(self, instance, timeout=0, retry_interval=0):
        aws_node = self._get_node_by_uuid(instance.uuid)
        if aws_node:
            aws_node.stop()

    def get_info(self, instance):
        aws_node = self._get_node_by_uuid(instance.uuid)

        if aws_node:
            node_power_state = POWER_STATE_MAP[aws_node.state['Code']]
            node_id = aws_node.id
        else:
            node_power_state = power_state.NOSTATE
            node_id = 0

        node_info = {
            'state':        node_power_state,
            'max_mem_kb':   0,  # '(int) the maximum memory in KBytes allowed',
            'mem_kb':       0,  # '(int) the memory in KBytes used by the instance',
            'num_cpu':      0,  # '(int) the number of virtual CPUs for the instance',
            'cpu_time_ns':  0,  # '(int) the CPU time used in nanoseconds',
            'id':           node_id
        }

        return node_info

    def reboot(self, instance, *args, **kwargs):
        aws_node = self._get_node_by_uuid(instance.uuid)
        if aws_node:
            aws_node.reboot()

    def attach_volume(self, context, connection_info, instance, mountpoint,
                      disk_bus=None, device_type=None, encryption=None):
        """Attach the disk to the instance at mountpoint using info."""
        pass

    def detach_volume(self, connection_info, instance, mountpoint,
                      encryption=None):
        """Detach the disk attached to the instance."""
        raise NotImplementedError()

    def _get_node_by_uuid(self, uuid):
        aws_nodes = list(self.driver.instances.filter(Filters=[{'Name': 'tag:openstack_server_id', 'Values': [uuid]}]))
        return aws_nodes[0] if aws_nodes else None
