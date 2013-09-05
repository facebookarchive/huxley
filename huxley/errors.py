class TestError(RuntimeError):

    def __init__(self, message, errorlist=[]):
        self.message = message
        self.errorlist = errorlist

    def __str__(self):
        return repr(self.message + '\n' + '\n'.join([str(item) for item in self.errorlist]))

