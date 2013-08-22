from ovirtsdk.api import API
from ovirtsdk.xml import params
from time import sleep
from lxml import etree
import util
import libvirt

from vm import VM
from printer import show, notify
import locals


class VirtBackend(object):

    def __init__(self):
        pass

    def create_vm(name):
        """
        Returns the VM object. Should require only the name parameter,
        the rest of the parameters should be either positional with defaults
        or passed via *args / **kwargs.
        """

        raise NotImplementedError("Backend class needs to override this")


class RHEVM(VirtBackend):

    def __init__(self, url, username, password, cluster_name, ca_file,
                 **kwargs):
        super(RHEVM, self).__init__()

        self.url = url
        self.username = username
        self.password = password
        self.cluster = cluster_name
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

    def make_snapshot(self, name):
        show('Creating new snapshot')
        pass

    def create_vm(self, name, memory=locals.MEMORY,
                  template=locals.TEMPLATE_NAME):
        """Creates a VM from given parameters and returns its hostname."""

        show('VM creation:')
        show.tab()

        # Set VM's parameters as defined in locals.py
        pars = params.VM(name=name,
                         memory=memory,
                         cluster=self.api.clusters.get(self.cluster),
                         template=self.api.templates.get(template))

        # locals.HOST can be used to enforce usage of a particular host
        if locals.HOST is not None:
            pars.set_placement_policy(params.VmPlacementPolicy(
                                         host=self.api.hosts.get(locals.HOST),
                                         affinity='pinned'))

        # Check whether the template exist, if so, create the VM
        if self.api.templates.get(template) is None:
            raise ValueError('Template does not exist.')
        vm = self.api.vms.add(pars)
        show('VM was created from Template successfully')

        # Set corret permissions so that VM can be seen in WebAdmin
        admin_vm_manager_perm = params.Permission(
                                    role=self.api.roles.get('UserVmManager'),
                                    user=self.api.users.get('admin'))

        vm.permissions.add(admin_vm_manager_perm)
        show('Permissions for admin to see VM set')

        # VM automatically shuts down after creation
        show('Waiting for VM to reach Down status')
        while self.api.vms.get(name).status.state != 'down':
            sleep(1)

        if self.api.vms.get(name).status.state != 'up':
            show('Starting VM')
            vm.start()
            while self.api.vms.get(name).status.state != 'up':
                sleep(1)

        # Obtain the IP address. It can take a while for the guest agent
        # to start, so we wait 2 minutes here before giving up.
        show('Waiting to obtain IP address')
        show('Press CTRL+C to interrupt and enter manually.')
        counter = 0
        try:
            while self.get_ip(name) is None:
                counter = counter + 1
                if counter > 120:
                    break
                sleep(1)
        except KeyboardInterrupt:
            counter = 100000

        if counter <= 120:
            ip = self.get_ip(name)
            last_ip_segment = ip.split('.')[-1]
            show("IP address of the VM is %s" % ip)
        else:
            notify('Enter the IP manually.')

            last_ip_segment = ''

            while not (len(last_ip_segment) > 0 and len(last_ip_segment) < 4):
                last_ip_segment = raw_input("IP address could not be "
                "determined. Enter the VM number (no leading zeros):")
                ip = locals.IP_BASE + last_ip_segment

        # Update the description
        desc = ''
        if len(last_ip_segment) == 1:
            desc = "00%s" % last_ip_segment
        elif len(last_ip_segment) == 2:
            desc = "0%s" % last_ip_segment
        else:
            desc = last_ip_segment

        # Set the VM's description so that it can be identified in WebAdmin
        vm = self.api.vms.get(name)
        vm.set_description(desc)
        vm.update()

        show("Description set to %s" % desc)

        # Necessary because of RHEV bug
        show("Pinging the VM")
        output, errors, rc = util.run(['ping', '-c', '3', ip])

        show.untab()

        return VM(name=name, backend=self, hostname='vm-%s' % desc,
                  domain=locals.DOMAIN, ip=ip)

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

    def get_ip(self, name):
        if self.api.vms.get(name).get_guest_info():
            return self.api.vms.get(name).get_guest_info()\
                       .get_ips().get_ip()[0].get_address()

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


class LibVirt(VirtBackend):

    def __init__(self, **kwargs):
        super(LibVirt, self).__init__()
        self.conn = libvirt.open(None)

        if self.conn is None:
            raise RuntimeError("Failed to connect to the hypervisor.")

    # empty implementation
    def check_arguments(self, name, template, connect):
        pass

    def make_snapshot(self, name):
        pass

    def get_domain(self, name):
        try:
            domain = self.conn.lookupByName(name)
        except:
            raise RuntimeError("VM with name {name} does not exist."
                               .format(name=name))

        return domain

    def get_ip(self, name):
        domain = self.get_domain(name)
        desc = etree.fromstring(domain.XMLDesc(0))
        macAddr = desc.find("devices/interface[@type='network']/mac")\
                      .attrib["address"].lower().strip()

        output, errors, rc = util.run(['arp', '-n'])

        if rc == 0:
            lines = [line.split() for line in output.split("\n")[1:]]
            matching = [line[0] for line in lines
                                if line and line[2] == macAddr]

            if matching:
                return matching[0]

    def start(self, name):
        if self.get_domain(name):
            output, errors, rc = util.run(['virsh',
                                           'start',
                                           name,
                                         ])

            #FIXME: this requires tweaking
            sleep(20)

            if rc != 0:
                raise RuntimeError("Could not start VM %s" % name)

    def create_vm(self, name, template=locals.TEMPLATE_NAME):

        # Check whether template VM exists
        template_domain = self.get_domain(template)

        # TODO: check if it is running, if is, print down warning and shut
        # it down

        if template_domain:
            output, errors, rc = util.run(['virt-clone',
                                           '-o',
                                           template,
                                           '--auto-clone',
                                           '-n',
                                           name,
                                         ])

            if rc != 0:
                raise RuntimeError("Could not clone VM %s" % template)

            self.start(name)

            ip = self.get_ip(name)

            return VM(name=name, backend=self, hostname=None,
                      domain=locals.DOMAIN, ip=ip)

    def reboot_vm(self, name):
        domain = self.get_domain(name)

        if domain.reboot() != 0:
            raise RuntimeError('VM reboot was not successful: {name}'
                               .format(name=name))