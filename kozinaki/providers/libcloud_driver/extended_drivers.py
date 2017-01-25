from libcloud.utils.py3 import httplib
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.common.linode import API_ROOT


def get_extended_driver(driver_cls):
    extended_drivers = {
        'Vultr': VultrNodeDriverExt,
        'Linode': LinodeNodeDriverExt,
    }

    return extended_drivers[driver_cls.name] if driver_cls.name in extended_drivers.keys() else driver_cls


class VultrNodeDriverExt(get_driver(Provider.VULTR)):

    def ex_shutdown_node(self, node):
        params = {'SUBID': node.id}
        res = self.connection.post('/v1/server/halt', params)

        return res.status == httplib.OK

    def ex_power_on_node(self, node):
        params = {'SUBID': node.id}
        res = self.connection.post('/v1/server/start', params)

        return res.status == httplib.OK


class LinodeNodeDriverExt(get_driver(Provider.LINODE)):

    def ex_shutdown_node(self, node):
        params = {"api_action": "linode.shutdown", "LinodeID": node.id}
        self.connection.request(API_ROOT, params=params)
        return True

    def ex_power_on_node(self, node):
        params = {"api_action": "linode.boot", "LinodeID": node.id}
        self.connection.request(API_ROOT, params=params)
        return True
