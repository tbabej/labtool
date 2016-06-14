from ovirtsdk.api import API
from ovirtsdk.xml import params
from ovirtsdk.infrastructure import errors as ovirterrors
from time import sleep
from lxml import etree
import util
import libvirt

from vm import VM
from printer import show, notify
import locals
import six

class VirtBackend(object):

    def __init__(self):
        self.verbose = 0
        pass

    def create_vm(self, name):
        """
        Returns the VM object. Should require only the name parameter,
        the rest of the parameters should be either positional with defaults
        or passed via *args / **kwargs.
        """

        raise NotImplementedError("Backend class needs to override this")


class RHEVM(VirtBackend):

    def __init__(self, url, cluster_name, ca_file, username=None,
                 password=None, kerberos=None, verbose=0, **kwargs):
        super(RHEVM, self).__init__()

        self.url = url
        self.username = username
        self.password = password
        self.cluster = cluster_name
        self.ca_file = ca_file
        self.kerberos = kerberos
        self.verbose = verbose
        self.debug = verbose > 1

        if self.kerberos:
            if self.verbose:
                show("Using Kerberos authentication")
            self.api = API(url=self.url,
                           kerberos=True,
                           ca_file=self.ca_file,
                           filter=True,
                           debug=self.debug
                           )
        else:
            if self.verbose:
                show("Using username and password: %s" % self.username)
            self.api = API(url=self.url,
                           username=self.username,
                           password=self.password,
                           ca_file=self.ca_file,
                           debug=self.debug)

    def create_record(self, *args, **kwargs):
        pass

    def get_vm(self, name, attempts=4):
        for i in range(attempts):
            vm = self.api.vms.get(name)
            if vm:
                return vm
        raise ValueError('Given VM name %s does not exist' % name)

    def get_snapshot(self, name, snapshot_name):
        candidates = [snap for snap in self.get_vm(name).snapshots.list()
                      if snap.get_description() == snapshot_name]

        if len(candidates) == 1:
            return candidates[0]
        else:
            return None

    def make_snapshot(self, name):
        show("Deleting all previous snapshots")
        show.tab()

        self.shutdown(name)

        for snap in self.get_vm(name).snapshots.list():
            if snap.get_description() != 'Active VM':
                show("Deleting snapshot: %s" % snap.get_description())
                snap.delete()

        while len(self.get_vm(name).snapshots.list()) > 1:
            show("Waiting for the deletion to complete.")
            sleep(5)

        show.untab()

        try:
            snapshot = params.Snapshot(description=locals.SNAPSHOT_NAME,
                                       vm=self.get_vm(name))
            self.get_vm(name).snapshots.add(snapshot)
            show("Creating a Snapshot")
            show('Waiting for Snapshot creation to finish')
            while self.get_vm(name).status.state == 'image_locked':
                sleep(5)
        except Exception as e:
            show('Failed to Create a Snapshot:\n%s' % str(e))

        if self.get_snapshot(name, locals.SNAPSHOT_NAME):
            show("Snapshot created: %s" % locals.SNAPSHOT_NAME)

        show.untab()

    def revert_to_snapshot(self, name):
        show.tab()

        self.stop(name)

        show('Restoring the snapshot: %s' % locals.SNAPSHOT_NAME)
        snapshot = self.get_snapshot(name, locals.SNAPSHOT_NAME)
        if not snapshot:
            raise ValueError("Snapshot %s does not exist"
                             % locals.SNAPSHOT_NAME)

        snapshot.restore()

        # VM automatically shuts down after creation
        show('Waiting for VM to reach Down status')
        while self.get_vm(name).status.state != 'down':
            sleep(15)
        show.untab()
        return self.load_vm(name)

    def check_arguments(self, name, template, connect):

        if connect:
            show('Checking whether given VM exists')
            self.get_vm(name)
        else:
            show('Checking whether given template exists')
            if util.get_latest_template(self.api, template) is None:
                raise ValueError('Template %s does not exist' % template)

            show('Checking whether given VM name is not used')
            if self.get_vm(name):
                raise ValueError('Given VM name %s is already used' % name)

    def get_vm_state(self, name, vm=None):
        # expect that vm object doesn't have to have a status object
        if not vm:
            vm = self.get_vm(name)
        if vm.status:
            return vm.status.state
        return None

    def create_vm(self, name, memory=locals.MEMORY,
                  template=locals.TEMPLATE_NAME):
        """Creates a VM from given parameters and returns its hostname."""

        show('VM creation:')
        show.tab()
        show('Name: %s' % name)
        show('Template: %s' % template)
        show('Memory: %s' % memory)

        tmpl = self.api.templates.get(template)
        if not tmpl:
            raise ValueError('Template does not exist: %s' % template)

        # # Check whether the template exist, if so, create the VM
        # if util.get_latest_template(self.api, template) is None:
        #     raise ValueError('Template does not exist: %s' % template)

        # Set VM's parameters as defined in locals.py
        pars = params.VM(name=name,
                         memory=memory,
                         cluster=self.api.clusters.get(self.cluster),
                         template=tmpl)

        # locals.HOST can be used to enforce usage of a particular host
        if locals.HOST:
            pars.set_placement_policy(params.VmPlacementPolicy(
                                         host=self.api.hosts.get(locals.HOST),
                                         affinity='pinned'))


        vm = self.api.vms.add(pars)
        show('VM was created from Template successfully')

        # Set corret permissions so that VM can be seen in WebAdmin
        if not self.kerberos:
            admin_vm_manager_perm = params.Permission(
                                        role=self.api.roles.get('UserVmManager'),
                                        user=self.api.users.get('admin'))

            vm.permissions.add(admin_vm_manager_perm)
            show('Permissions for admin to see VM set')

        # VM automatically shuts down after creation
        show('Waiting for VM to reach Down status')
        while self.get_vm_state(name, vm) != 'down':
            vm = self.get_vm(name)
            sleep(15)
        show.untab()
        return vm

    def start(self, name, vm=None, wait=True):
        if not vm:
            vm = self.get_vm(name)
        if self.get_vm_state(name, vm) == 'down':
            show('Starting VM')
            vm.start()

            while wait and self.get_vm_state(name, vm) != 'up':
                vm = self.get_vm(name)
                sleep(15)
        return vm

    def load_vm(self, name, vm=None):
        if not vm:
            vm = self.get_vm(name)
        vm = self.start(name, vm)

        # Obtain the IP address. It can take a while for the guest agent
        # to start, so we wait 2 minutes here before giving up.
        show('Waiting to obtain IP address')
        show('Press CTRL+C to interrupt and enter manually.')
        counter = 0
        ip = self.get_ip(vm)
        try:
            while ip is None:
                vm = self.get_vm(name)
                ip = self.get_ip(vm)
                counter = counter + 1
                if counter > 40:
                    break
                sleep(15)
        except KeyboardInterrupt:
            counter = 100000

        if counter <= 40:
            fqdn = vm.get_guest_info().fqdn
            show("IP address of the VM is %s" % ip)
            show("FQDN of the VM is %s" % fqdn)
        else:
            notify('Enter the IP manually.')
            fqdn = ''
            last_ip_segment = ''

            while not (len(last_ip_segment) > 0 and len(last_ip_segment) < 4):
                last_ip_segment = raw_input("IP address could not be "
                "determined. Enter the VM number (no leading zeros):")
                ip = locals.IP_BASE + last_ip_segment

        # Set the VM's description so that it can be identified in WebAdmin
        if fqdn:
            vm.set_description(fqdn)
            vm.update()
            show("Description set to %s" % fqdn)

        # Necessary because of RHEV bug
        show("Pinging the VM")
        output, errors, rc = util.run(['ping', '-c', '3', ip])

        show.untab()

        return VM(name=name, backend=self, hostname=fqdn,
                  domain=locals.DOMAIN, ip=ip)

    def reboot(self, name):
        show('Rebooting the VM:')
        show.tab()

        vm = self.get_vm(name)
        vm.shutdown()

        show('Waiting for VM to reach Down status')
        while self.get_vm_state(name, vm) != 'down':
            vm = self.get_vm(name)
            sleep(5)

        if self.get_vm_state(name, vm) != 'up':
            show('Starting VM')
            vm.start()
            show('Waiting for VM to reach Up status')
            while self.get_vm_state(name) != 'up':
                sleep(1)

        show('Waiting for all the services to start')
        sleep(60)

        show.untab()

    def get_ip(self, name_or_vm):
        vm = name_or_vm
        if isinstance(name_or_vm, six.string_types):
            vm = self.get_vm(name_or_vm)

        gi = vm.get_guest_info()
        if gi:
            return gi.get_ips().get_ip()[0].get_address()

    def stop(self, name):
        vm = self.get_vm(name)
        if self.get_vm_state(name, vm) != 'down':
            vm.stop()

            show('Waiting for VM %s to reach Down status' % name)
            while self.get_vm_state(name) != 'down':
                sleep(5)

            show('VM %s stopped successfully' % name)
        else:
            show('VM %s is already stopped' % name)

    def shutdown(self, name):
        self.get_vm(name).shutdown()

        show('Waiting for VM %s to reach Down status' % name)
        while self.get_vm_state(name) != 'down':
            sleep(5)

        show('VM %s stopped successfully' % name)

    def remove_vm(self, name):
        show('Removing the VM:')
        show.tab()

        try:
            vm = self.get_vm(name)
        except ValueError:
            show('Could not obtain VM. Probably does not exist.')
            return

        try:
            vm.stop()
            show('Waiting for VM to reach Down status')
        except Exception:
            show('Vm is not running.')
            pass

        while self.get_vm_state(name) != 'down':
            sleep(1)

        vm.delete()
        show('{name} was removed.'.format(name=name))
        show.untab()

    def exists(self, name):
        try:
            self.get_vm(name)
            return True
        except ValueError:
            return False

    def console(self, name):
        vm = self.get_vm(name)
        virtual_viewer_params = {}
        virtual_viewer_params['toggle-fullscreen'] = 'shift+f11'
        virtual_viewer_params['release-cursor'] = 'shift+f12'
        virtual_viewer_params['enable-smartcard'] = 0
        virtual_viewer_params['fullscreen'] = 0
        virtual_viewer_params['enable-usb-autoshare'] = 0
        virtual_viewer_params['title'] = 'VM %s - %%d - Press SHIFT+F12 to Release Cursor' % name
        try:
            virtual_viewer_params['type'] = vm.display.get_type()
            virtual_viewer_params['host'] = vm.display.address
            virtual_viewer_params['port'] = vm.display.port
            virtual_viewer_params['tls-port'] = vm.display.secure_port
            virtual_viewer_params['password'] = vm.ticket().get_ticket().get_value()
        except ovirterrors.RequestError as ex:
            raise RuntimeError(str(ex))

        return virtual_viewer_params


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
        # Delete all the snapshots for this VM
        for snap in self.get_domain(name).listAllSnapshots():
            show('Deleting snapshot %s' % snap.getName())
            snap.delete()

        show('Creating new snapshot..')
        stdout, stderr, rc = util.run(['virsh',
                                       'snapshot-create',
                                       '--domain',
                                       name
                                     ])

        show('Created!')

        if rc != 0:
            raise RuntimeError("Could not create snapshot for %s" % name)

    def revert_to_snapshot(self, name):
        show.tab()

        if len(self.get_domain(name).listAllSnapshots()) != 1:
            raise RuntimeError("Incorrect number of snapshots for %s" % name)

        show('Correct number of snapshots for %s' % name)

        snapshot = self.get_domain(name).listAllSnapshots()[0].getName()

        stdout, stderr, rc = util.run(['virsh',
                                       'snapshot-revert',
                                       '--domain',
                                       name,
                                       '--snapshotname',
                                       snapshot,
                                       '--force'
                                     ])

        if rc != 0:
            raise RuntimeError("Could not revert to snapshot for %s" % name)

        show('Revert successful')
        show.untab()

    def get_domain(self, name):
        try:
            domain = self.conn.lookupByName(name)
        except:
            raise RuntimeError("VM with name {name} does not exist."
                               .format(name=name))

        return domain

    def get_next_free_mac(self):
        used_macs = [etree.fromstring(dom.XMLDesc(0))
                    .find("devices/interface[@type='network']/mac")
                    .attrib["address"].lower().strip()
                    for dom in self.conn.listAllDomains()]

        all_macs = ['de:ad:be:ef:00:0%s' % i for i in range(2, 10)] + \
                   ['de:ad:be:ef:00:%s' % i for i in range(11, 21)]

        available_macs = list(set(all_macs) - set(used_macs))

        if available_macs:
            return available_macs[0]
        else:
            raise RuntimeError("No MACs available. You have defined too many "
                               "VMs.")

    def get_ip(self, name):
        domain = self.get_domain(name)
        desc = etree.fromstring(domain.XMLDesc(0))
        mac = desc.find("devices/interface[@type='network']/mac")\
                      .attrib["address"].lower().strip()

        # Macs are tied to the IPs
        last_mac_segment = mac.split(':')[-1]
        ip = locals.IP_BASE + '%s' % int(last_mac_segment)

        return ip

    def start(self, name):
        if self.get_domain(name) and not self.get_domain(name).isActive():
            show('Starting %s' % name)

            output, errors, rc = util.run(['virsh',
                                           'start',
                                           name,
                                           '--force-boot'
                                         ])

            sleep(20)

            if rc != 0:
                raise RuntimeError("Could not start VM %s" % name)

    def create_vm(self, name, template=locals.TEMPLATE_NAME):

        # TODO: check if the VM with the name of name exists

        # Check whether template VM exists
        show('Checking for existence of template')
        template_domain = self.get_domain(template)

        # TODO: check if it is running, if is, print down warning and shut
        # it down

        if template_domain:
            show('Cloning..')

            # Find out next available MAC address in the pool
            new_mac = self.get_next_free_mac()

            output, errors, rc = util.run(['virt-clone',
                                           '-o',
                                           template,
                                           '--auto-clone',
                                           '-n',
                                           name,
                                           '-m',
                                           new_mac,
                                         ])

            if rc != 0:
                raise RuntimeError("Could not clone VM %s" % template)

            show('Cloning successful')

            # TODO: check that it started, if not, wait
            show('Starting..')
            self.start(name)
            sleep(10)

            # Macs are tied to the IPs
            last_mac_segment = new_mac.split(':')[-1]
            ip = locals.IP_BASE + '%s' % int(last_mac_segment)

            show('IP determined: %s' % ip)
            hostname = util.normalize_hostname(ip)

            return VM(name=name, backend=self, hostname=hostname,
                      domain=locals.DOMAIN, ip=ip)

    def create_record(self, hostname, ip):
        show('Creating record in /etc/hosts')
        util.run(['sudo', 'sed', '-i', '/%s/d' % ip, '/etc/hosts'])
        with open('/etc/hosts', 'a') as f:
            f.write('{ip} {name}'.format(ip=ip, name=hostname))
        util.run(['sudo', 'systemctl', 'restart', 'libvirtd'])

    def load_vm(self, name):

        show('Loading VM %s' % name)
        self.get_domain(name)  # this fails if VM does not exist

        # TODO: check that it started, if not, wait
        self.start(name)

        # TODO: need a proper retry function
        ip = None
        timeout = 0

        while ip is None:
            ip = self.get_ip(name)
            sleep(2)
            timeout += 2

            if timeout > 20:
                raise RuntimeError("Could not determine IP of VM %s" % name)

        hostname = util.normalize_hostname(ip)
        show('IP determined: %s' % ip)

        return VM(name=name, backend=self, hostname=hostname,
                  domain=locals.DOMAIN, ip=ip)

    def reboot_vm(self, name):
        domain = self.get_domain(name)

        if domain.reboot() != 0:
            raise RuntimeError('VM reboot was not successful: {name}'
                               .format(name=name))

    def exists(self, name):
        domains = [dom.name() for dom in self.conn.listAllDomains()]
        return name in domains
