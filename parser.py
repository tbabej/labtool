import argparse
import locals
import sys

from printer import show
from vm import VM


def validateBuild(args):

        available_build_actions = ('branch', 'patch', 'origin')

        action = args.build[0]

        if args.install and (args.install[1] == 'repo' or
                             args.install[1] == 'develrepo'):
            raise Exception('First building IPA from sources and then '
                            'installing it from repo makes no sense. '
                            'Think about it.')

        if action not in available_build_actions:
            raise ValueError('Unknown build action: {s}. Choose either branch '
                             'or patch.'.format(s=action))

        if action == 'patch':
            show('Checking whether all given patches exist.')
            vm = VM(locals.NFS_VM, locals.DOMAIN, None, None,
                    set_sudoers=False)

            patches_exist = True

            for patch_id in args.build[1:]:
                num = vm.cmd('bash labtool/ipa-fun-get-patch-name.sh %s'
                             % patch_id, allow_failure=True, silent=True)

                if num != 0:
                    show('Inappropriate number of patches matching %s'
                          % patch_id)
                    patches_exist = False

                if not patches_exist:
                    raise ValueError("One of the given patches could not be "
                                     "determined.")

            show('Patch check successful.')
            vm.close()

        elif action == 'branch':
            pass  # check that such branch indeed exists


def validateInstall(args):
        available_sources = ('local', 'repo', 'develrepo')
        available_actions = ('ipa', 'packages')

        action = args.install[0]
        source = args.install[1]

        if source not in available_sources:
            raise ValueError('Unknown source: {s}. Choose either local '
                             'or repo or develrepo.'.format(s=source))

        if action not in available_actions:
            raise ValueError('Unknown action: {s}. Choose either ipa '
                             'or packages.'.format(s=action))

        if source == 'local' and args.build is None:
            # check that rpms are present or that build option is specified
            pass


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
                             'on top). For origin/master use: --build branch '
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

    parser.add_argument('--ipadevel',
                        nargs='+',
                        metavar=('PACKAGES'),
                        help='Use this option to specify packages that should'
                             'be installed from the ipa-devel repo.')

    parser.add_argument('--workspace',
                        help='Create workspace. This is not done automatically,'
                             ' since it is better (performance-wise) to do this'
                             ' once in the template.',
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

    #show('Running pre-setup checks:')
    #show.tab()

    # Additional option validation
    # TODO: support build validation in local VMs
    #if args.build and not args.local:
    #    validateBuild(args)
    #if args.install:
    #    validateInstall(args)

    return args
