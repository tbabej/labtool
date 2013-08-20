from printer import show
from paramiko import SSHClient, WarningPolicy
import warnings
from time import sleep
from subprocess import call

import locals

# Ignore incoming warnings from SSHClient about SSH keys mismatch
warnings.filterwarnings("ignore", category=UserWarning)


class VM():

    def __init__(self, name, backend, hostname, domain, ip, set_sudoers=True):
        "Creates a connection to the client"

        self.name = name
        self.backend = backend
        self.hostname = hostname
        self.domain = domain
        self.ip = ip
        self.fqdn = '%s.%s' % (self.hostname, self.domain)
        self.locals = dict()

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
            self.client.connect(self.ip, username=user)
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
                         " original {log}".format(**self.locals))
            except KeyboardInterrupt:
                show('Falling back to backup mirror')
                self.cmd("bash labtool/ipa-fun-create-workspace.sh"
                         " backup {log}".format(**self.locals))

            # apply patches on top of fresh master branch
            if action[0] == 'patch':
                # sync the patches
                call('patchsync')
                sleep(15)

                for patch_id in action[1:]:
                    show('Applying patch {patch}'.format(patch=patch_id))
                    self.cmd("bash labtool/ipa-fun-apply-patch.sh"
                             " {patch} {log}".format(
                                 patch=patch_id, **self.locals))

        elif action[0] == 'branch':

            # clone new FreeIPA repository
            show('Creating workspace for this build')
            try:
                self.cmd("bash labtool/ipa-fun-create-workspace.sh"
                         " original {log}".format(**self.locals))
            except KeyboardInterrupt:
                show('Falling back to backup mirror')
                self.cmd("bash labtool/ipa-fun-create-workspace.sh"
                         " backup {log}".format(**self.locals))

            # Checkout to given branch
            show('Checking out to {branch}'.format(
                branch=action[1]))
            self.cmd("bash labtool/ipa-fun-checkout.sh"
                     " {branch} {log}".format(
                         branch=action[1], **self.locals))

        self.install_dependencies('no', 'build')

        show('Building sources')
        self.cmd("bash labtool/ipa-fun-build.sh"
                 " {log}".format(**self.locals))

        show.untab()

    def install_dependencies(self, devel, build):
        if devel == 'devel':
            show('Ipa-devel repository allowed')
        show('Installing dependencies')
        self.cmd("bash labtool/ipa-fun-install-dependencies.sh"
                 " {build} {devel} {log}".format(devel=devel, build=build,
                                                 **self.locals))

    def install_packages(self, action):
        # in either way install packages
        if action[1] == 'local':
            if self.locals.get('dest') != self.hostname:
                show('Installing local rpm packages'
                     .format(**self.locals))
            else:
                show('Installing local rpm packages')

            self.cmd("bash labtool/ipa-fun-install-rpms.sh"
                     " {log}".format(**self.locals))

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
        self.backend.reboot(self.name)
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