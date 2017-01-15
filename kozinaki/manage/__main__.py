import os
import sys
import argparse

import yaml
import libcloud
import click
import click_spinner
from terminaltables import AsciiTable

from .manage import NodeManager

DEFAULT_LANG = 'en'
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help'], 'max_content_width': 160}

with open(os.path.join(BASE_PATH, 'config.yaml'), 'r') as conf_file:
    CONFIG = yaml.load(conf_file)

# Get node manager
node_manager = NodeManager()


# NODE COMMANDS
class NodeCommand(click.MultiCommand):
    def list_commands(self, ctx):
        return CONFIG['services']['commands']

    def get_command(self, ctx, name):
        cmd = self.create_cmd(name)
        return cmd

    def create_cmd(self, cmd_action):

        option_name = click.Argument(['name'], nargs=-1)

        cmd = click.Command(
            name=cmd_action,
            params=[option_name],
            help='{} all node services'.format(cmd_action.capitalize()),
            callback=self.cmd_callback
        )

        return cmd

    def cmd_callback(self, names_set):
        ctx = click.get_current_context()
        for node_name in names_set:
            node = node_manager.node_get(node_name=node_name)
            if node:
                response = node.command(cmd=ctx.command.name)
                for r in response:
                    print(r)
            else:
                click.secho('Node "{}" not found'.format(node_name), fg='red')


# CREATE PROVIDER NODES
class NodeProviderCreate(click.MultiCommand):
    def __init__(self, **attrs):
        super(NodeProviderCreate, self).__init__(**attrs)
        self.spinner = click_spinner.Spinner()

    def format_commands(self, ctx, formatter):
        """Extra format methods for multi methods that adds all the commands after the options."""
        native_providers = []
        libcloud_providers = []

        list_commands = self.list_commands(ctx)
        max_provider_name_ident = len(max(list_commands, key=len))

        for subcommand in list_commands:
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command.  Ignore it
            if cmd is None:
                continue

            subcommand = subcommand.ljust(max_provider_name_ident)

            help = cmd.short_help or ''
            if subcommand[0].islower():
                native_providers.append((subcommand, help))
            else:
                libcloud_providers.append((subcommand, help))

        if native_providers or libcloud_providers:
            with formatter.section(click.style('Providers', fg='green')):

                if native_providers:
                    with formatter.section(click.style('Native clients', fg='yellow')):
                        formatter.write_dl(sorted(native_providers))

                if libcloud_providers:
                    with formatter.section(click.style('Libcloud ({}) clients'.format(libcloud.__version__),
                                                       fg='yellow')):
                        formatter.write_dl(sorted(libcloud_providers))

        self.spinner.stop()

    def list_commands(self, ctx):
        self.spinner.start()
        return node_manager.valid_node_types['providers'].keys()

    def get_command(self, ctx, name):
        cmd = self.create_command(name)
        return cmd

    def create_command(self, provider_name):
        config = node_manager.valid_node_types['providers'][provider_name]

        provider_options = [
            click.Option(param_decls=['--name'], help='Compute node name', required=True)
        ]

        for param, param_data in node_manager.get_node_params(provider_name).items():
            argument_params = dict()
            argument_params['help'] = ''

            description = param_data.get('description', {}).get(DEFAULT_LANG)
            default = param_data.get('default')
            arg_type = param_data.get('type')

            if description:
                argument_params['help'] += '{} '.format(description)
            if arg_type:
                argument_params['help'] += '(type: {}) '.format(arg_type)
            if default:
                argument_params.update({
                    'default': default,
                    'required': False
                })
                argument_params['help'] += '(default: {}) '.format(default)
            else:
                argument_params['required'] = True

            provider_options.append(click.Option(
                param_decls=['--{}'.format(param)],
                help=argument_params['help'],
                default=default,
                required=False if default else True
            ))

        cmd = click.Command(
            name=provider_name,
            params=provider_options,
            help=click.style(config['description'], fg='cyan'),
            short_help=click.style(config['description'], fg='cyan'),
            callback=self.create_node_callback
        )

        return cmd

    def create_node_callback(self, name, compute_driver, **kwargs):
        with click_spinner.spinner():
            ctx = click.get_current_context()
            print(name, compute_driver, kwargs)
            print(ctx.command.name)
            # node_manager.node_create(node_name=node_name, node_type=ctx.command.name, **vars(kwargs))


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
@click.option('--verbose', '-v', is_flag=True, help="Will print verbose messages.")
def main(verbose):
    pass


@main.command('list')
def node_list():
    """Show all created compute nodes"""
    table_data = [['Name', 'Type', 'Services']]
    for node in node_manager.node_list():
        table_data.append([node.name, node.type, ','.join(service for service in node.services)])
    table = AsciiTable(table_data)
    print(table.table)


@main.group(cls=NodeProviderCreate)
def create():
    """Create compute node for cloud provider"""
    pass


@main.command()
@click.confirmation_option()
@click.argument('name')
def delete(name):
    """Delete compute node"""
    click.echo(name)


@main.group('cmd', cls=NodeCommand)
def node_commands():
    """Send command to node services"""
    pass


def main_old():
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
