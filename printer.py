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