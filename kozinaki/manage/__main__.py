import os
import sys
import argparse

import yaml
from terminaltables import AsciiTable

from .manage import NodeManager

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
DEFAULT_LANG = 'en'

with open(os.path.join(BASE_PATH, 'config.yaml'), 'r') as conf_file:
    CONFIG = yaml.load(conf_file)


def main():
    # Get node manager
    node_manager = NodeManager()

    # Formatter
    formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width=200)

    parser = argparse.ArgumentParser(description='ApexView compute node manage utility')
    subparsers = parser.add_subparsers(help='Available actions', dest='action')

    # CREATE
    parser_create = subparsers.add_parser(
        'create',
        description='Create compute node for cloud provider',
        help='Create new nova compute node'
    )
    parser_create_subparsers = parser_create.add_subparsers(help='Available cloud providers', dest='type')

    # Create providers subparsers
    for provider_name, config in node_manager.valid_node_types['providers'].items():
        parser_create_type = parser_create_subparsers.add_parser(
            provider_name,
            description='Create node in {} cloud'.format(provider_name.upper()),
            help='Create node in {} cloud'.format(provider_name.upper()),
            formatter_class=formatter_class
        )
        parser_create_type.add_argument('--name', type=str, required=True, help='Compute node name (type: str)')
        for param, param_data in node_manager.get_node_params(provider_name).items():
            argument_params = dict()
            argument_params['help'] = ''

            description = param_data.get('description', {}).get(DEFAULT_LANG)
            default = param_data.get('default')
            arg_type = param_data.get('type')

            if description:
                argument_params['help'] += '{} '.format(description)
            if arg_type:
                argument_params['type'] = getattr(sys.modules['builtins'], arg_type)
                argument_params['help'] += '(type: {}) '.format(arg_type)
            if default:
                argument_params.update({
                    'default': default,
                    'required': False
                })
                argument_params['help'] += '(default: {}) '.format(default)
            else:
                argument_params['required'] = True

            parser_create_type.add_argument('--{}'.format(param), **argument_params)

    # DELETE
    parser_delete = subparsers.add_parser(
        'delete',
        description='Delete compute node',
        help='Delete compute node'
    )
    parser_delete.add_argument('--name', type=str, required=True, help='Compute node name')

    # LIST
    parser_node_list = subparsers.add_parser(
        'list',
        description='Show all created compute nodes',
        help='Show all created compute nodes'
    )

    # COMMANDS
    for command in CONFIG['services']['commands']:
        parser_node_command = subparsers.add_parser(
            command,
            description='Pass {} command to all node services'.format(command),
            help='Pass {} command to all node services'.format(command)
        )
        parser_node_command.add_argument('--name', type=str, required=True, help='Compute node name')

    args = parser.parse_args()

    if args.action == 'create':
        node_manager.node_create(node_name=args.name, node_type=args.type, **vars(args))
    elif args.action == 'delete':
        node_manager.node_delete(node_name=args.name)
    elif args.action == 'list':
        table_data = [['Name', 'Type', 'Services']]
        for node in node_manager.node_list():
            table_data.append([node.name, node.type, ','.join(service for service in node.services)])
        table = AsciiTable(table_data)
        print(table.table)
    elif args.action in CONFIG['services']['commands']:
        node = node_manager.node_get(node_name=args.name)
        response = node.command(cmd=args.action)
        for r in response:
            print(r)

    else:
        parser.print_help()
