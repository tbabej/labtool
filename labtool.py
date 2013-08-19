#! /usr/bin/python

import argparse
import sys

from printer import show, notify
from backend import RHEVM
from vm import VM

# Import sensitive settings
import locals


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

def main(args):
    show('***** Welcome to LabTool *****')
    show('')

    if not args.local:
        show('Estabilishing connection to RHEVM lab')
        rhevm = RHEVM(locals.URL, locals.USERNAME, locals.PASSWORD,
                      locals.CLUSTER_NAME, locals.CA_FILE)

    # We need to remove the VM before running check_arguments()
    if args.remove:
        rhevm.remove_vm(args.name)

    show('Running pre-setup checks:')
    show.tab()

    # Additional option validation
    # TODO: support build validation in local VMs
    if args.build and not args.local:
        validateBuild(args)
    if args.install:
        validateInstall(args)

    if not args.local:
        rhevm.check_arguments(args.name, args.template, args.connect)

    show.untab()

    show('Setting up: %s' % args.name)
    show.tab()

    if args.connect:
        hostname = rhevm.get_description(args.name)
    elif args.local:
        hostname = args.name.split('.')[0]
        locals.DOMAIN = 'ipa.com'
        rhevm = None
    else:
        hostname = rhevm.create_vm(args.name, locals.MEMORY, args.template,
                                   'auto')

    if args.lab[0] == 'BOS':
        vm = VM(hostname, locals.DOMAIN, rhevm, args.name)
    else:
        vm = VM(hostname, locals.DOMAIN, rhevm, args.name)

    # If we wanted a clean VM, we finish here
    if args.clean:
        return

    # Setup logging path
    log_path = ">> ~/%s.log  2>&1" % hostname
    vm.set_format(log=log_path, dest='')

    vm.clean_log()

    devel = 'no'
    build = 'no'

    if args.install and args.install[1] == 'develrepo':
        devel = 'devel'

    if args.build:
        vm.set_format(dest=hostname)
        vm.build(args.build)
        build = 'build'

    elif args.source:
        vm.set_format(dest='vm-%s' % args.source)

    if args.install:
        show('Preparing:')
        show.tab()
        if not args.build:
            vm.install_dependencies(devel, build)
        vm.install_packages(args.install)
        show.untab()

        if args.install[0] == 'ipa':
            show.tab()
            vm.prepare_install(args.firewall, args.selinux, args.trust)
            show.untab()
            vm.install_ipa()

            show('Post-install configuration:')
            show.tab()
            vm.check_services()
            show.untab()

            if args.test:
                vm.run_tests()

            if args.trust:
                vm.setup_trust()

    show.untab()

    if args.replicas:
        replicas = []

        for i in range(0, args.replicas):
            replica_name = args.name + 'r%d' % (i + 1)

            show('Setting up: %s' % replica_name)
            show.tab()

            hostname = rhevm.create_vm(replica_name, locals.MEMORY,
                                       args.template, 'auto')

            vm.prepare_replica(hostname)

            if args.lab[0] == 'BOS':
                replicas.append(VM(hostname, locals.DOMAIN, rhevm, replica_name,
                                 set_sudoers=False))
            else:
                replicas.append(VM(hostname, locals.DOMAIN, rhevm,
                                   replica_name))

            # Setup logging path
            log_path = ">> ~/%s.log  2>&1" % hostname
            replicas[i].set_format(log=log_path, dest='')

            if args.source:
                replicas[i].set_format(dest='vm-%s' % args.source)
            elif args.build:
                replicas[i].set_format(dest=vm.hostname)

            if args.install:
                show('Preparing:')
                show.tab()
                vm.install_dependencies(devel, build)
                replicas[i].install_packages(args.install)
                show.untab()

                if args.install[0] == 'ipa':
                    show.tab()

                    replicas[i].prepare_install(args.firewall,
                                                args.selinux,
                                                args.trust,
                                                subdomain=vm.hostname)
                    replicas[i].add_nameserver(vm.hostname)
                    show.untab()
                    replicas[i].install_replica(vm.hostname)

                    show('Post-install configuration:')
                    show.tab()
                    vm.check_services()
                    show.untab()

                if args.trust:
                    replicas[i].setup_trust(hostname=vm.hostname)

            show.untab()

    if args.clients:
        clients = []

        for i in range(0, args.clients):
            client_name = args.name + 'c%d' % (i + 1)

            show('Setting up: %s' % client_name)
            show.tab()

            hostname = rhevm.create_vm(client_name, locals.MEMORY,
                                       args.template, 'auto')

            if args.lab[0] == 'BOS':
                clients.append(VM(hostname, locals.DOMAIN, rhevm, client_name,
                                 set_sudoers=False))
            else:
                clients.append(VM(hostname, locals.DOMAIN, rhevm, client_name))

            # Setup logging path
            log_path = ">> ~/%s.log  2>&1" % hostname
            clients[i].set_format(log=log_path, dest='')

            if args.source:
                clients[i].set_format(dest='vm-%s' % args.source)
            elif args.build:
                clients[i].set_format(dest=vm.hostname)

            clients[i].install_packages(args.install)

            if args.trust:
                clients[i].set_hostname(subdomain=vm.hostname)

            clients[i].install_client(vm.hostname)

            show.untab()


if __name__ == '__main__':
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

    try:
        main(args)
    except Exception, e:
        print '***The command above has FAILED***'
        print 'You can find the logs in ~/<hostname>.log on the VM'
        print ''
        print str(e)

        notify('Scripts on %s failed?!' % args.name)

        sys.exit(1)

    notify('Scripts on %s finished :-)' % args.name)
