#! /usr/bin/python

import sys
import time

from printer import show, notify, monitor
from parser import parse_options
from vm import VM

# Import sensitive settings
import locals
import util
import backend as backends


def main(args):
    show('***** Welcome to LabTool *****')
    show('')

    if locals.REQUIRE_ROOT:
        util.require_root()

    BackendClass = getattr(backends, locals.BACKEND)

    show('Estabilishing connection to %s lab' % locals.BACKEND)

    backend = BackendClass(url=locals.URL,
                           username=locals.USERNAME,
                           password=locals.PASSWORD,
                           cluster_name=locals.CLUSTER_NAME,
                           ca_file=locals.CA_FILE)

    # We need to remove the VM before running check_arguments()
    #if args.remove:
    #    backend.remove_vm(args.name)

    #if not args.local:
    #    backend.check_arguments(args.name, args.template, args.connect)

    #show.untab()

    show('Setting up: %s' % args.name)
    show.tab()

    #elif args.local:
    #    hostname = args.name.split('.')[0]
    #    locals.DOMAIN = 'ipa.com'
    #else:

    if backend.exists(args.name) and not args.connect:
        show('VM exists, reverting back to snapshot')
        try:
            backend.revert_to_snapshot(args.name)
        except ValueError as e:
            if args.remove:
                show(str(e) + ': removing the whole VM')
                backend.remove_vm(args.name)
            else:
                raise Exception(str(e) + ': use --remove if you want '
                                'to remove whole VM')

    if not backend.exists(args.name):
        if args.connect:
            raise Exception("You requested --connect but specified VM does not "
                            "exist, exiting.")

        vm = backend.create_vm(args.name,
                               template=args.template or locals.TEMPLATE_NAME)
    else:
        vm = backend.load_vm(args.name)

    vm.connect()
    vm.setup_logging_path()

    monitor(vm.hostname, vm.domain)

    if args.workspace or not vm.detect_workspace():
        vm.create_workspace()
    vm.update_workspace()

    backend.make_snapshot(args.name)
    while True:
        try:
            vm.start()
            break
        except Exception, e:
            # vm.start() can fail if disks are not in state 'down'
            show("Skipping error %s" % str(e))
            time.sleep(5)
            pass

    vm.connect()

    # Install selected packages from ipa-devel repo
    if args.ipadevel:
        vm.install_devel_packages(packages=args.ipadevel)

    show.untab()

    if args.build:
        vm.build(args.build)

    # Setup a new hostname
    vm.set_hostname(trust=args.trust)

    if args.install:
        show('Preparing:')

        # Installs FreeIPA packages either from local source or from repository
        vm.install_packages(args.install)

        if args.install[0] == 'ipa':
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

################### Replicas and clients untested and not working ATM #########
    if args.replicas:
        replicas = []

        for i in range(0, args.replicas):
            replica_name = args.name + 'r%d' % (i + 1)

            show('Setting up: %s' % replica_name)
            show.tab()

            hostname = backend.create_vm(replica_name, locals.MEMORY,
                                         args.template)

            vm.prepare_replica(hostname)

            if args.lab[0] == 'BOS':
                replicas.append(VM(hostname, locals.DOMAIN, backend, replica_name,
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

            vm = backend.create_vm(client_name, locals.MEMORY,
                                   args.template, 'auto')

            clients.append(vm)

            # Setup logging path
            clients[i].set_format(log=log_path, log_file=log_file)

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
    args = parse_options()

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
