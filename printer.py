import dbus
import sys
try:
    import locals
except ImportError:
    sys.exit("Error: configuration is missing. "
             "Use locals.py.in as basics and create locals.py")

class Printer():

    def __init__(self):
        self.prefix = ''

    def __call__(self, text):
        print(self.prefix + text)

    def tab(self, space=' '):
        self.prefix = self.prefix + 4 * space

    def untab(self):
        self.prefix = self.prefix[:-4]

    def debug(self, msg):
        if locals.DEBUG:
            print('[DEBUG]: ' + msg)


def notify(body, headline='Labtool Ready!', app_name='LabTool', app_icon='',
        timeout=50000, actions=[], hints=[], replaces_id=0):
    try:
        _bus_name = 'org.freedesktop.Notifications'
        _object_path = '/org/freedesktop/Notifications'
        _interface_name = _bus_name

        session_bus = dbus.SessionBus()
        obj = session_bus.get_object(_bus_name, _object_path)
        interface = dbus.Interface(obj, _interface_name)
        interface.Notify(app_name, replaces_id, app_icon,
                headline, body, actions, hints, timeout)
    except Exception:
        print body


def monitor(hostname, domain):
    try:
        bus_name = 'org.kde.konsole'
        object_path = '/Konsole'
        interface_name = 'org.kde.konsole.Window'

        session_bus = dbus.SessionBus()
        obj = session_bus.get_object(bus_name, object_path)
        interface = dbus.Interface(obj, interface_name)

        session = interface.newSession()

        object_path = '/Sessions/%s' % session
        interface_name = 'org.kde.konsole.Session'

        session_bus = dbus.SessionBus()
        obj = session_bus.get_object(bus_name, object_path)
        interface = dbus.Interface(obj, interface_name)

        logfile = getattr(locals, 'LOG_FILE', None) or '/vmlog'
        user = getattr(locals, 'USER', None)

        interface.sendText("ssh -n %s@%s.%s 'sudo tail -f %s'" %
                           (user, hostname, domain, logfile))
        interface.sendText("\n")
    except:
        pass

show = Printer()
