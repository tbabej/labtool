import dbus
import locals


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


show = Printer()