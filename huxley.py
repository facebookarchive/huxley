# TODO: keypress and scroll events

import contextlib
import operator
import os
import time
import jsonpickle
from selenium import webdriver
import Image
import ImageChops
import plac

def images_identical(path1, path2):
    im1 = Image.open(path1)
    im2 = Image.open(path2)
    return ImageChops.difference(im1, im2).getbbox() is None    

def image_diff(path1, path2, outpath, diffcolor):
    im1 = Image.open(path1)
    im2 = Image.open(path2)
    pix1 = im1.load()
    pix2 = im2.load()
    
    if im1.mode != im2.mode:
        raise ValueError('Different pixel modes between %r and %r' % (path1, path2))
    if im1.size != im2.size:
        raise ValueError('Different dimensions between %r and %r' % (path1, path2))

    mode = im1.mode

    if mode == '1':
        value = 255
    elif mode == 'L':
        value = 255
    elif mode == 'RGB':
        value = diffcolor
    elif mode == 'RGBA':
        value = diffcolor + (255,)
    elif mode == 'P':
        raise NotImplementedError('TODO: look up nearest palette color')
    else:
        raise NotImplementedError('Unexpected PNG mode')

    width,height = im1.size

    for y in xrange(height):
        for x in xrange(width):
            if pix1[x,y] != pix2[x,y]:
                pix2[x, y] = value
    im2.save(outpath)

class TestError(RuntimeError):
    pass

class TestStep(object):
    def __init__(self, offset_time):
        self.offset_time = offset_time

    def execute(self, run):
        raise NotImplementedError

class ClickTestStep(TestStep):
    CLICK_ID = '_jonxClick'
    def __init__(self, offset_time, pos):
        super(ClickTestStep, self).__init__(offset_time)
        self.pos = pos

    def execute(self, run):
        print '  Clicking', self.pos
        # Work around a bug in ActionChains.move_by_offset()
        id = run.d.execute_script('return document.elementFromPoint(%d, %d).id;' % tuple(self.pos))
        if id is None:
            run.d.execute_script('document.elementFromPoint(%d, %d).id = %r;' % (self.pos[0], self.pos[1], self.CLICK_ID))
            id = self.CLICK_ID
        run.d.find_element_by_id(id).click()

class ScreenshotTestStep(TestStep):
    def __init__(self, offset_time, run, index):
        super(ScreenshotTestStep, self).__init__(offset_time)
        self.index = index
        
    def get_path(self, test):
        return os.path.join(test.path, 'screenshot' + str(self.index) + '.png')

    def execute(self, run):
        print '  Taking screenshot', self.index
        original = self.get_path(run.test)
        new = os.path.join(run.test.path, 'last.png')
        if run.mode == TestRunModes.RERECORD:
            run.d.save_screenshot(original)
        else:
            run.d.save_screenshot(new)
            if not images_identical(original, new):
                image_diff(original, new, os.path.join(run.test.path, 'diff.png'), run.diffcolor)
                raise TestError('Screenshot %r was different; compare it with last.png. See diff.png for the comparison.' % self.index)

class Test(object):
    def __init__(self, url, screen_size, start_time, path):
        self.steps = []
        self.url = url
        self.screen_size = screen_size
        self.last_timestamp = start_time
        self.path = path

class TestRunModes(object):
    RECORD = 1
    RERECORD = 2
    PLAYBACK = 3

class TestRun(object):
    def __init__(self, test, d, mode, diffcolor):
        self.test = test
        self.d = d
        self.mode = mode
        self.diffcolor = diffcolor

    @classmethod
    def rerecord(cls, test, d, diffcolor):
        print 'Begin rerecord'
        run = TestRun(test, d, TestRunModes.RERECORD, diffcolor)
        run._playback()

    @classmethod
    def playback(cls, test, d, diffcolor):
        print 'Begin playback'
        run = TestRun(test, d, TestRunModes.PLAYBACK, diffcolor)
        run._playback()

    def _playback(self):
        self.d.set_window_size(*self.test.screen_size)
        self.d.get('about:blank')
        self.d.refresh()
        self.d.get(self.test.url)
        last_offset_time = 0
        for step in self.test.steps:
            sleep_time = step.offset_time - last_offset_time
            print '  Sleeping for', sleep_time, 'ms'
            time.sleep(float(sleep_time) / 1000)
            step.execute(self)
            last_offset_time = step.offset_time

    @classmethod
    def record(cls, d, url, screen_size, path, diffcolor, remote_d):
        print 'Begin record'
        if not remote_d:
            remote_d = d
        try:
            os.makedirs(path)
        except:
            pass
        start_time = d.execute_script('return Date.now();')
        test = Test(url, screen_size, start_time, path)
        run = TestRun(test, d, TestRunModes.RECORD, diffcolor)
        d.set_window_size(*screen_size)
        d.get('about:blank')
        d.refresh()
        d.get(test.url)
        d.execute_script('''
(function() {
var events = [];
window.addEventListener('click', function (e) { events.push([Date.now(), [e.clientX, e.clientY]]); }, true);
window._getJonxEvents = function() { return events; };
})();
''')
        steps = []
        while True:
            if len(raw_input("Press enter to take a screenshot, or type Q+enter if you're done\n")) > 0:
                break
            screenshot_step = ScreenshotTestStep(d.execute_script('return Date.now();') - start_time, run, len(steps))
            run.d.save_screenshot(screenshot_step.get_path(run.test))
            steps.append(screenshot_step)
            print len(steps), 'screenshots taken'

        # now capture the clicks
        events = d.execute_script('return window._getJonxEvents();')
        for (timestamp, id) in events:
            steps.append(ClickTestStep(timestamp - start_time, id))
            
        steps.sort(key=operator.attrgetter('offset_time'))

        test.steps = steps

        cls.rerecord(test, remote_d, diffcolor)
        cls.playback(test, remote_d, diffcolor)

        return test

DRIVERS = {
    'firefox': webdriver.Firefox,
    'chrome': webdriver.Chrome,
    'ie': webdriver.Ie,
    'opera': webdriver.Opera
}

CAPABILITIES = {
    'firefox': webdriver.DesiredCapabilities.FIREFOX,
    'chrome': webdriver.DesiredCapabilities.CHROME,
    'ie': webdriver.DesiredCapabilities.INTERNETEXPLORER,
    'opera': webdriver.DesiredCapabilities.OPERA
}

@plac.annotations(
    filename=plac.Annotation('Test file location'),
    record=plac.Annotation('URL to open for test recording', 'option', 'r', metavar='URL'),
    rerecord=plac.Annotation('Re-run the test but take new screenshots', 'flag', 'R'),
    browser=plac.Annotation('Browser to use, either firefox, chrome, phantomjs, ie or opera.', 'option', 'b', str, metavar='NAME'),
    remote=plac.Annotation('Remote WebDriver to use', 'option', 'w', metavar='URL'),
    diffcolor=plac.Annotation('Diff color for errors (i.e. 0,255,0)', 'option', 'd', str, metavar='RGB'),
    screensize=plac.Annotation('Width and height for screen (i.e. 1024x768)', 'option', 's', metavar='SIZE'),
)
def main(filename, record=None, rerecord=False, browser='firefox', remote=None, diffcolor='0,255,0', screensize='1024x768'):
    try:
        d = DRIVERS[browser]()
        screensize = tuple(int(x) for x in screensize.split('x'))
    except KeyError:
        raise ValueError(
            'Invalid browser %r; valid browsers are %r.' % (browser, DRIVERS.keys())
        )
    try:
        os.makedirs(filename)
    except:
        pass

    diffcolor = tuple(int(x) for x in diffcolor.split(','))
    jsonfile = os.path.join(filename, 'record.json')

    with contextlib.closing(d):
        if record:
            remote_d = None
            if remote:
                remote_d = webdriver.Remote(remote_d, CAPABILITIES[browser])
            with open(jsonfile, 'w') as f:
                f.write(jsonpickle.encode(TestRun.record(d, record, screensize, filename, diffcolor, remote_d)))
                print 'Test recorded successfully'
        elif rerecord:
            with open(jsonfile, 'r') as f:
                TestRun.rerecord(jsonpickle.decode(f.read()), d, diffcolor)
                print 'Test rerecorded successfully'
        else:
            with open(jsonfile, 'r') as f:
                TestRun.playback(jsonpickle.decode(f.read()), d, diffcolor)
                print 'Test played back successfully'

if __name__ == '__main__':
    plac.call(main)
