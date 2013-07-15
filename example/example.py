import huxley

class Example(huxley.HuxleyTestCase):
    def test_toggle(self):
        self.huxley(
            filename='example.huxley',
            url='http://localhost:8000/example.html',
            sleepfactor=.1
        )

huxley.unittest_main()
