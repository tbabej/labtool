from ovirtsdk.api import API
from ovirtsdk.xml import params

from printer import show, notify
from time import sleep


class VirtBackend(object):

    def __init__(self):
        pass


class RHEVM(VirtBackend):

    def __init__(self, url, username, password, cluster, ca_file):
        super(VirtBackend, self).__init__()

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
