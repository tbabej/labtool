#! /usr/bin/python

import argparse
import sys
from ovirtsdk.api import API
from ovirtsdk.xml import params
from time import sleep
from paramiko import SSHClient, WarningPolicy
import warnings
import dbus


# Import sensitive settings
import locals


# Ignore incoming warnings from SSHClient about SSH keys mismatch
warnings.filterwarnings("ignore", category=UserWarning)


def notify(body, headline='Labtool Ready!', app_name='LabTool', app_icon='',
        timeout=50000, actions=[], hints=[], replaces_id=0):
    _bus_name = 'org.freedesktop.Notifications'
    _object_path = '/org/freedesktop/Notifications'
    _interface_name = _bus_name

    session_bus = dbus.SessionBus()
    obj = session_bus.get_object(_bus_name, _object_path)
    interface = dbus.Interface(obj, _interface_name)
    interface.Notify(app_name, replaces_id, app_icon,
            headline, body, actions, hints, timeout)


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


class Printer():

    def __init__(self):
        self.prefix = ''
        self.silence = False

    def __call__(self, text):
        if not self.silence:
            print(self.prefix + text)

    def tab(self, space=' '):
        self.prefix = self.prefix + 4 * space

    def untab(self):
        self.prefix = self.prefix[:-4]

    def silence(self):
        self.silence = True

    def talk(self):
        self.silence = False

show = Printer()


class RHEVM():

    def __init__(self, url, username, password, cluster, ca_file):

        self.url = url
        self.username = username
        self.password = password
        self.cluster = cluster
        self.ca_file = ca_file

        self.api = API(url=self.url,
                       username=self.username,
                       password=self.password,
                       ca_file=self.ca_file)

    def check_arguments(self, name, template, connect):

        if connect:
            show('Checking whether given VM exists')
            if self.api.vms.get(name) is None:
                raise ValueError('Given VM name %s does not exist' % name)
        else:
            show('Checking whether given template exists')
            if self.api.templates.get(template) is None:
                raise ValueError('Template %s does not exist' % template)

            show('Checking whether given VM name is not used')
            if self.api.vms.get(name) is not None:
                raise ValueError('Given VM name %s is already used' % name)

    def create_vm(self, name, memory, template, desc):
        """Creates a VM from given parameters and returns its hostname."""

        show('VM creation:')
        show.tab()

        pars = params.VM(name=name,
                         memory=memory,
                         description=desc,
                         cluster=self.api.clusters.get(self.cluster),
                         template=self.api.templates.get(template))

        if locals.HOST is not None:
            pars.set_placement_policy(params.VmPlacementPolicy(
                                         host=self.api.hosts.get(locals.HOST),
                                         affinity='pinned'))

        if self.api.templates.get(template) is None:
            raise ValueError('Template does not exist.')

        vm = self.api.vms.add(pars)

        show('VM was created from Template successfully')

        admin_vm_manager_perm = params.Permission(
                                    role=self.api.roles.get('UserVmManager'),
                                    user=self.api.users.get('admin'))

        vm.permissions.add(admin_vm_manager_perm)
        show('Permissions for admin to see VM set')

        show('Waiting for VM to reach Down status')
        while self.api.vms.get(name).status.state != 'down':
            sleep(1)

        if self.api.vms.get(name).status.state != 'up':
            show('Starting VM')
            vm.start()
            while self.api.vms.get(name).status.state != 'up':
                sleep(1)

        show('Waiting to obtain IP address')
        show('Press CTRL+C to interrupt and enter manually.')
        counter = 0
        try:
            while self.api.vms.get(name).get_guest_info() is None:
                counter = counter + 1
                if counter > 120:
                    break
                sleep(1)
        except KeyboardInterrupt:
            counter = 100000

        if counter <= 120:
            ip = self.api.vms.get(name).get_guest_info()\
                     .get_ips().get_ip()[0].get_address()

            show("IP address of the VM is %s" % ip)

            desc = ip.split('.')[-1]
        else:
            notify('Enter the IP manually.')

            desc = ''

            while not (len(desc) > 0 and len(desc) < 4):
                desc = raw_input("IP address could not be determined. "
                                 "Enter the VM number (no leading zeros):")

        if len(desc) == 1:
            desc = "00%s" % desc
        elif len(desc) == 2:
            desc = "0%s" % desc
        hostname = "vm-%s" % desc

        vm = self.api.vms.get(name)
        vm.set_description(hostname)
        vm.update()

        show("Description set to %s" % hostname)

        show.untab()

        return hostname

    def reboot(self, name):
        show('Rebooting the VM:')
        show.tab()

        vm = self.api.vms.get(name)
        vm.shutdown()

        show('Waiting for VM to reach Down status')
        while self.api.vms.get(name).status.state != 'down':
            sleep(1)

        if self.api.vms.get(name).status.state != 'up':
            show('Starting VM')
            vm.start()
            show('Waiting for VM to reach Up status')
            while self.api.vms.get(name).status.state != 'up':
                sleep(1)

        show('Waiting for all the services to start')
        sleep(60)

        show.untab()

    def get_description(self, name):
        vm = self.api.vms.get(name)
        return vm.get_description()

    def remove_vm(self, name):
        show('Removing the VM:')
        show.tab()

        vm = self.api.vms.get(name)
        if vm is None:
            show('Could not obtain VM. Probably does not exist.')
            return

        try:
            vm.stop()
            show('Waiting for VM to reach Down status')
        except Exception:
            show('Vm is not running.')
            pass

        while self.api.vms.get(name).status.state != 'down':
            sleep(1)

        vm.delete()
        show('{name} was removed.'.format(name=name))
        show.untab()


class VM():

    def __init__(self, hostname, domain, rhevm, name, set_sudoers=True):
        "Creates a connection to the client"

        self.hostname = hostname
        self.domain = domain
        self.fqdn = '%s.%s' % (self.hostname, self.domain)
        self.rhevm = rhevm
        self.locals = dict()
        self.name = name

        if set_sudoers:
            show('Configuring sudo commands execution in sudoers')
            show('Using root login')
            self.connect(user='root')
            self.cmd('sed -i.bak "s/Defaults    requiretty'
                     '/# Defaults    requiretty/g" /etc/sudoers')
            self.close()

        self.connect()

    def connect(self, user=locals.USER):
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(WarningPolicy())

        # show('Connecting to %s' % self.fqdn)
        try:
            self.client.connect(self.fqdn, username=user)
        except UserWarning:
            pass

    def get_connection(self):
        return self.client

    def cmd(self, command, allow_failure=False, silent=False):
        i, o, e = self.client.exec_command(command)

        if not silent:
            for line in o.readlines():
                show(line.strip())
            for line in e.readlines():
                show(line.strip())

        return_code = o.channel.recv_exit_status()

        if return_code == 0 or allow_failure:
            return return_code
        else:
            raise RuntimeError("The following command failed: %s" % command)

    def close(self):
        self.client.close()
        # show('Connection to %s closed' % self.fqdn)

    def clean_log(self):
        show('Removing previous log file for this VM')
        self.cmd("rm -f ~/%s.log" % self.hostname)

    def add_nameserver(self, hostname):
        ip = locals.IP_BASE + hostname.split('-')[1].lstrip('0')
        show('Adding ' + ip + ' as nameserver')
        self.cmd('sudo sed -i.bak "2a\\nameserver ' + ip + '" /etc/resolv.conf')

    def build(self, action):
        show('Building:')
        show.tab()

        if action[0] == 'patch'\
            or action[0] == 'origin' and action[1] == 'master':

            # clone new FreeIPA repository
            show('Creating workspace for this build')
            try:
                self.cmd("bash labtool/ipa-fun-create-workspace.sh"
                         " original {dest} {log}".format(**self.locals))
            except KeyboardInterrupt:
                show('Falling back to backup mirror')
                self.cmd("bash labtool/ipa-fun-create-workspace.sh"
                         " backup {dest} {log}".format(**self.locals))

            # apply patches on top of fresh master branch
            if action[0] == 'patch':
                for patch_id in action[1:]:
                    show('Applying patch {patch}'.format(patch=patch_id))
                    self.cmd("bash labtool/ipa-fun-apply-patch.sh"
                             " {patch} {dest} {log}".format(
                                 patch=patch_id, **self.locals))

        elif action[0] == 'branch':

            # clone new FreeIPA repository
            show('Creating workspace for this build')
            try:
                self.cmd("bash labtool/ipa-fun-create-workspace.sh"
                         " original {dest} {log}".format(**self.locals))
            except KeyboardInterrupt:
                show('Falling back to backup mirror')
                self.cmd("bash labtool/ipa-fun-create-workspace.sh"
                         " backup {dest} {log}".format(**self.locals))

            # Checkout to given branch
            show('Checking out to {branch}'.format(
                branch=action[1]))
            self.cmd("bash labtool/ipa-fun-checkout.sh"
                     " {branch} {dest} {log}".format(
                         branch=action[1], **self.locals))

        self.install_dependencies('no', 'build')

        show('Building sources')
        self.cmd("bash labtool/ipa-fun-build.sh"
                 " {dest} {log}".format(**self.locals))

        show.untab()

    def install_dependencies(self, devel, build):
        if devel == 'devel':
            show('Ipa-devel repository allowed')
        show('Installing dependencies')
        self.cmd("bash labtool/ipa-fun-install-dependencies.sh"
                 " {devel} {build} {log}".format(devel=devel, build=build,
                                                 **self.locals))

    def install_packages(self, action):
        # in either way install packages
        if action[1] == 'local':
            if self.locals.get('dest') != self.hostname:
                show('Installing local rpm packages from {dest}'
                     .format(**self.locals))
            else:
                show('Installing local rpm packages')

            self.cmd("bash labtool/ipa-fun-install-rpms.sh"
                     " {dest} {log}".format(**self.locals))

        elif action[1] == 'repo' or action[1] == 'develrepo':
            show('Installing packages from repositories')
            self.cmd("bash labtool/ipa-fun-install-repo.sh"
                     " {log}".format(**self.locals))

    def set_hostname(self, subdomain=''):
            show('Changing hostname')
            self.cmd("bash labtool/ipa-set-hostname.sh"
                     " {subdomain} {log}".format(subdomain=subdomain,
                                                **self.locals))

    def prepare_install(self, firewall, selinux, trust, subdomain=''):

        # set firewall
        show('Setting firewall')
        if firewall:
            switch = "on"
        else:
            switch = "off"

        self.cmd("bash labtool/ipa-set-firewall.sh"
                " {setting} {log}".format(setting=switch, **self.locals))

        # set SELinux
        show('Setting SELinux')
        if selinux:
            switch = "on"
        else:
            switch = "off"

        self.cmd("bash labtool/ipa-set-selinux.sh"
                 " {setting} {log}".format(setting=switch, **self.locals))

        # this changes the hostname to vm-xyz.domxyz.tbad.$DOMAIN
        if trust:
            self.set_hostname(subdomain=subdomain)

        # apply current workarounds
        show('Applying workarounds for IPA install to work')
        self.cmd("bash labtool/ipa-fun-current-workarounds.sh"
                 " {log}".format(**self.locals))

    def install_ipa(self):
        # install IPA
        show('Installing IPA')
        self.cmd("bash labtool/ipa-fun-install-ipa.sh"
                 " {log}".format(**self.locals))

    def run_tests(self):
        show('Testing:')
        show.tab()

        # run the test suite
        show('Configuring VM for tests')
        self.cmd("bash labtool/ipa-fun-setup-tests.sh"
                 " {log}".format(**self.locals))

        show('Running whole test suite')
        ret = self.cmd("bash labtool/ipa-fun-run-tests.sh"
                       " {dest} {log}".format(**self.locals),
           allow_failure=True)

        if ret == 0:
            show('PASSED. See {log} for the logs.'.format(**self.locals))
        else:
            show('FAILED. See {log} for the logs.'.format(**self.locals))

        show.untab()

    def setup_trust(self, hostname=''):
        show('Setting up AD Trust:')
        show.tab()

        show('Configuring VM')
        self.cmd("bash labtool/ipa-fun-setup-trust1.sh"
                 " {hostname} {log}".format(hostname=hostname, **self.locals))

        # We need to reboot the VM to setup trust
        show('Rebooting:')
        show.tab()

        self.close()
        self.rhevm.reboot(self.name)
        self.connect()

        show.untab()

        show('Post-reboot trust configuration')
        ret = self.cmd("bash labtool/ipa-fun-setup-trust2.sh"
                       " {log}".format(**self.locals), allow_failure=True)
        if ret:
            show('Trust setup failed.')

        show.untab()

    def set_format(self, **kwargs):
        self.locals.update(kwargs)

    def prepare_replica(self, hostname):
        show('Creating replica file for {replica}'.format(replica=hostname))
        self.cmd("bash labtool/ipa-fun-prepare-replica.sh"
               " {replica} {log}".format(replica=hostname, **self.locals))

    def install_replica(self, master):
        # TODO: support for replica install settings
        show('Installing replica')
        ret = self.cmd("bash labtool/ipa-fun-install-replica.sh"
                       " {master} {log}".format(master=master, **self.locals),
                        allow_failure=True)
        if ret:
            show('Replica installation failed.')

    def check_services(self):
        ret = self.cmd("bash labtool/ipa-fun-check-services.sh",
                       allow_failure=True)
        if ret:
            show('Service check failed.')

    def install_client(self, master):
        # TODO: support for replica install settings
        show('Installing client')
        ret = self.cmd("bash labtool/ipa-fun-install-client.sh"
                       " {master} {log}".format(master=master, **self.locals),
                        allow_failure=True)
        if ret:
            show('Client installation failed.')


def main(args):
    show('***** Welcome to LabTool *****')
    show('')

    show('Estabilishing connection to RHEVM lab')
    rhevm = RHEVM(locals.URL, locals.USERNAME, locals.PASSWORD,
                  locals.CLUSTER_NAME, locals.CA_FILE)

    # We need to remove the VM before running check_arguments()
    if args.remove:
        rhevm.remove_vm(args.name)

    show('Running pre-setup checks:')
    show.tab()

    # Additional option validation
    if args.build:
        validateBuild(args)
    if args.install:
        validateInstall(args)

    rhevm.check_arguments(args.name, args.template, args.connect)

    show.untab()

    show('Setting up: %s' % args.name)
    show.tab()

    if args.connect:
        hostname = rhevm.get_description(args.name)
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
