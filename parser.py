import argparse
import locals
import sys


def parse_options():
    parser = argparse.ArgumentParser(
        description='Tool to simplify testing and development in RHEVM lab.')

    parser.add_argument('--lab',
                        nargs=1,
                        help='Either BOS or BRQ',
                        default=[locals.DEFAULT_LOCATION],
                        required=False)

    parser.add_argument('--template',
                        help='The template from which the VM should be '
                             'created.',
                        required=False)

    parser.add_argument('--clean',
                        help='Creates a clean VM.',
                        action='store_true')

    parser.add_argument('--firewall',
                        help='Turn the firewall on.',
                        action='store_true')

    parser.add_argument('--selinux',
                        help='Put SELinux into enforcing mode.',
                        action='store_true')

    parser.add_argument('--debug',
                        help='Just for option validation testing.',
                        action='store_true')

    parser.add_argument('--build',
                        nargs='+',
                        metavar=('WHAT', 'WHICH'),
                        help='Build the rpms from selected source (master, '
                             'selected branch, or master with selected patch '
                             'on top). For origin/master use: --build origin '
                             'master. For branch use: --build branch '
                             'BRANCHNAME. For patch use: --build patch '
                             'PATCHNUMBER [PATCHNUMBER..]')

    parser.add_argument('--source',
                        metavar='NUM',
                        help='VM number for sources / prepared rpms. This is '
                             'not needed to specify when using --build option')

    parser.add_argument('--replicas',
                        metavar='NUM',
                        type=int,
                        help='The number of replicas to be created.')

    parser.add_argument('--clients',
                        metavar='NUM',
                        type=int,
                        help='The number of replicas to be created.')

    parser.add_argument('--install',
                        nargs=2,
                        metavar=('WHAT', 'FROM'),
                        help='WHAT is either ipa or packages. FROM is either '
                             'rpms or repo or develrepo. ',
                        required=False)

    parser.add_argument('--trust',
                        help='Setup trust with global AD server in the lab.',
                        action='store_true')

    parser.add_argument('--test',
                        help='Run unit test suite. Use with --install ipa'
                             'option only.',
                        action='store_true')

    parser.add_argument('--connect',
                        help='Do not create a new VM but rather connect '
                             'to existing one.',
                        action='store_true')

    parser.add_argument('--remove',
                        help='Remove VM in case it already exists.',
                        action='store_true')

    parser.add_argument('--local',
                        help='Flag that makes sure name is used as hostname.',
                        action='store_true')

    parser.add_argument('--name',
                        help='The name of VM in the lab.',
                        required=True)

    args = parser.parse_args()

    # Set global variables
    locals.set_locale(args.lab[0])

    if args.template is None:
        args.template = locals.TEMPLATE_NAME

    if args.debug:
        sys.exit(0)

    return args
