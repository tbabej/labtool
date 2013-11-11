from printer import show
from paramiko import SSHClient, WarningPolicy
import warnings
from time import sleep

import locals
import util

# Ignore incoming warnings from SSHClient about SSH keys mismatch
warnings.filterwarnings("ignore", category=UserWarning)


class VM():

    def __init__(self, name, backend, hostname, domain, ip):
        "Creates a connection to the client"

        self.name = name
        self.backend = backend
        self.hostname = hostname
        self.domain = domain
        self.ip = ip
        self.fqdn = '%s.%s' % (self.hostname, self.domain)
        self.locals = dict()

        show.debug("New VM object!")
        show.debug("Name: %s" % self.name)
        show.debug("Backend: %s" % self.backend)
        show.debug("Hostname: %s" % self.hostname)
        show.debug("Domain: %s" % self.domain)
        show.debug("IP: %s" % self.ip)

    def set_sudoers(self):
        show('Configuring sudo commands execution in sudoers')
        show('Using root login')
        self.connect(user='root')
        self.cmd('sed -i.bak "s/Defaults    requiretty'
                 '/# Defaults    requiretty/g" /etc/sudoers')
        self.close()

    def connect(self, user=locals.USER):
        # show('Connecting to %s' % self.fqdn)
        success = False
        timeout = 0

        show('Connecting..')

        while not (success or timeout > 60):
            try:
                self.client = SSHClient()
                self.client.set_missing_host_key_policy(WarningPolicy())
                self.client.connect(self.ip, username=user,
                                    key_filename=locals.PRIVATE_KEY)
                success = True
            except UserWarning:
                show.debug('UserWarning ignored')
            except Exception, e:
                show.debug('Caught exception: %s' % e)
                sleep(2)
                timeout += 2

        if timeout > 60:
            raise RuntimeError("Could not connect to the %s" % self.ip)

        show('Connection successful!')

    def get_connection(self):
        return self.client

    def cmd(self, command, allow_failure=False, silent=False):
        i, o, e = self.client.exec_command('set -o pipefail; ' + command)

        def print_out(line):
            if silent:
                show(line.strip())
            else:
                show.debug(line.strip())

        # It is important to print output here at least at the debug level
        # to empty the buffer
        for line in o.readlines():
            print_out(line)
        for line in e.readlines():
            print_out(line)

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
        self.cmd("rm -f %s" % self.locals['log_file'])

    def add_nameserver(self, hostname):
        show('Adding ' + self.ip + ' as nameserver')
        self.cmd('sudo sed -i.bak "2a\\nameserver '
                 + self.ip + '" /etc/resolv.conf')

    def update_workspace(self):
        show('Updating workspace - pulling updates for FreeIPA and LabTool')
        self.cmd("bash labtool/ipa-fun-update-workspace.sh"
                 " {log}".format(**self.locals))

    def setup_logging_path(self):
        log_file = getattr(locals, 'LOGFILE', None) or '/vmlog'
        log_path = "2>&1 | sudo tee -a {f}".format(f=log_file)
        self.set_format(log=log_path, log_file=log_file)

    def build(self, build_args):
        show('Building:')
        show.tab()

        if build_args[0] == 'patch':
            show('Syncing the patches:')
            # TODO: make this generic
            util.run(['rsync', '-rc', '--delete', '/home/tbabej/Work/patches',
                      '%s:dev/' % self.ip])

            for patch_id in build_args[1:]:
                show('Applying patch {patch}'.format(patch=patch_id))
                self.cmd("bash labtool/ipa-fun-apply-patch.sh"
                         " {patch} {log}".format(patch=patch_id,
                                                 **self.locals))

        elif build_args[0] == 'branch':
            show('Checking out to {branch}'.format(branch=build_args[1]))
            self.cmd("bash labtool/ipa-fun-checkout.sh"
                     " {branch} {log}".format(branch=build_args[1],
                                              **self.locals))
        else:
            raise RuntimeError("Unknown action: %s" % build_args[0])

        show('Installing build dependencies')
        self.install_build_dependencies()

        show('Applying build workarounds')
        self.apply_build_workarounds()

        show('Building sources')
        self.cmd("bash labtool/ipa-fun-build.sh"
                 " {log}".format(**self.locals))

        show.untab()

    def create_workspace(self):
        show('Creating workspace. You should really do this in the template!')
        self.cmd("echo test")
        self.cmd("bash labtool/ipa-fun-create-workspace.sh"
                 " {log}".format(**self.locals))

    def install_devel_packages(self, packages=[]):
        if packages:
            show('Installing packages from devel repo: {pckgs}'
                 .format(pckgs=', '.join(packages)))
            self.cmd('sudo yum install -y --enablerepo=ipa-devel {pckgs}'
                     .format(pckgs=' '.join(packages)))

    def install_build_dependencies(self):
        self.cmd("bash labtool/ipa-fun-install-build-dependencies.sh"
                 " {log}".format(**self.locals))

    def apply_build_workarounds(self):
        pass

    def install_packages(self, action):
        if action[1] == 'local':
            show('Installing local rpm packages')
            self.cmd("bash labtool/ipa-fun-install-rpms.sh"
                     " {log}".format(**self.locals))

        elif action[1] == 'repo':
            show('Installing packages from repositories')
            self.cmd("bash labtool/ipa-fun-install-repo.sh"
                     " {log}".format(**self.locals))

    def set_hostname(self, trust=False, subdomain='',
                     domain=locals.DOMAIN):

        last_ip_segment = self.ip.split('.')[-1]
        hostname = self.hostname

        if trust:
            hostname += '.dom{ip_id}.tbad'.format(
                ip_id=util.normalize_ip_suffix(last_ip_segment))

        hostname += '.' + self.domain

        self.hostname = hostname
        show('Setting hostname to %s' % hostname)

        self.cmd("bash labtool/ipa-set-hostname.sh"
                 " {hostname} {log}".format(hostname=hostname,
                                            **self.locals))

        show('Creating DNS record for the VM')
        self.backend.create_record(hostname=self.hostname, ip=self.ip)

    def prepare_install(self, firewall, selinux, trust, subdomain=''):

        # Set firewall
        if firewall:
            switch = "on"
        else:
            switch = "off"

        show('Setting firewall {setting}'.format(setting=switch))
        self.cmd("bash labtool/ipa-set-firewall.sh"
                " {setting} {log}".format(setting=switch, **self.locals))

        # set SELinux
        if selinux:
            switch = "on"
        else:
            switch = "off"

        show('Setting SELinux {setting}'.format(setting=switch))
        self.cmd("bash labtool/ipa-set-selinux.sh"
                 " {setting} {log}".format(setting=switch, **self.locals))

        # Apply current workarounds
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
                       " {log}".format(**self.locals),
           allow_failure=True)

        if ret == 0:
            show('PASSED. See {log} for the logs.'.format(**self.locals))
        else:
            show('FAILED. See {log} for the logs.'.format(**self.locals))

        show.untab()

    def setup_trust(self, hostname=''):
        show('Setting up AD Trust..')

        self.cmd("bash labtool/ipa-fun-setup-trust.sh"
                 " {hostname} {log}".format(hostname=hostname, **self.locals))

        show('Completed!')

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
