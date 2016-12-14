import os
import argparse

import yaml
from terminaltables import AsciiTable

from .manage import NodeManager

BASE_PATH = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(BASE_PATH, 'config.yaml'), 'r') as conf_file:
    CONFIG = yaml.load(conf_file)


class StoreNameValuePair(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        for val in values:
            n, v = val.split('=')
            setattr(namespace, n, v)


def main():

    valid_commands = CONFIG['nodes']['commands']
    valid_commands.extend(CONFIG['services']['commands'])

    parser = argparse.ArgumentParser()
    parser.add_argument('action', metavar='action', type=str, nargs=1, help='Command', choices=valid_commands)
    action_arg = parser.parse_known_args()

    node_manager = NodeManager()

    if action_arg[0].action == ['create']:
        parser.add_argument('name', metavar='name', type=str, nargs=1, help='Node name')
        parser.add_argument('type', metavar='type', type=str, nargs=1, help='Node type')
        parser.add_argument('config', nargs='*', action=StoreNameValuePair, help='Node config options')
        args = parser.parse_args()
        node_manager.node_create(node_name=args.name[0], node_type=args.type[0], **vars(args))

    elif action_arg[0].action == ['delete']:
        parser.add_argument('name', metavar='name', type=str, nargs=1, help='Node name')
        args = parser.parse_args()
        node_manager.node_delete(node_name=args.name[0])

    elif action_arg[0].action == ['show']:
        parser.add_argument('type', metavar='type', type=str, nargs='?', help='Node type')
        args = parser.parse_args()
        if args.type:
            node_params = node_manager.get_node_params(node_type=args.type)
            print('Need to provide: {}'.format(node_params))
        else:
            print('Valid node types:')
            for type_name, config in node_manager.valid_node_types.items():
                print('{}: {}'.format(type_name, config))

    elif action_arg[0].action == ['list']:
        all_nodes = node_manager.node_list()
        table_data = [
            ['Name', 'Type', 'Services']
        ]
        for node in all_nodes:
            table_data.append([node.name, node.type, ','.join(service for service in node.services)])
        table = AsciiTable(table_data)
        print(table.table)

    else:
        parser.add_argument('name', metavar='name', type=str, nargs=1, help='Node name')
        args = parser.parse_args()
        node = node_manager.node_get(node_name=args.name[0])
        node.command(cmd=action_arg[0].action[0])
