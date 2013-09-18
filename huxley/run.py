# Copyright (c) 2013 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import operator
import os
import time

from huxley.consts import TestRunModes
from huxley.errors import TestError
from huxley.steps import ScreenshotTestStep, ClickTestStep, KeyTestStep

def get_post_js(url, postdata):
    markup = '<form method="post" action="%s">' % url
    for k in postdata.keys():
        markup += '<input type="hidden" name="%s" />' % k
    markup += '</form>'

    js = 'var container = document.createElement("div"); container.innerHTML = %s;' % json.dumps(markup)

    for (i, v) in enumerate(postdata.values()):
        if not isinstance(v, basestring):
            # TODO: is there a cleaner way to do this?
            v = json.dumps(v)
        js += 'container.children[0].children[%d].value = %s;' % (i, json.dumps(v))

    js += 'document.body.appendChild(container);'
    js += 'container.children[0].submit();'
    return '(function(){ ' + js + '; })();'


def navigate(d, url):
    href, postdata = url
    d.get('about:blank')
    d.refresh()
    if not postdata:
        d.get(href)
    else:
        d.execute_script(get_post_js(href, postdata))


class Test(object):
    def __init__(self, screen_size):
        self.steps = []
        self.screen_size = screen_size


class TestRun(object):
    def __init__(self, test, path, url, d, mode, diffcolor, save_diff):
        if not isinstance(test, Test):
            raise ValueError('You must provide a Test instance')
        self.test = test
        self.path = path
        self.url = url
        self.d = d
        self.mode = mode
        self.diffcolor = diffcolor
        self.save_diff = save_diff

    @classmethod
    def rerecord(cls, test, path, url, d, sleepfactor, diffcolor, save_diff):
        print 'Begin rerecord'
        run = TestRun(test, path, url, d, TestRunModes.RERECORD, diffcolor, save_diff)
        run._playback(sleepfactor)
        print
        print 'Playing back to ensure the test is correct'
        print
        cls.playback(test, path, url, d, sleepfactor, diffcolor, save_diff)

    @classmethod
    def playback(cls, test, path, url, d, sleepfactor, diffcolor, save_diff):
        print 'Begin playback'
        run = TestRun(test, path, url, d, TestRunModes.PLAYBACK, diffcolor, save_diff)
        run._playback(sleepfactor)

    def _playback(self, sleepfactor):
        self.d.set_window_size(*self.test.screen_size)
        navigate(self.d, self.url)
        last_offset_time = 0
        for step in self.test.steps:
            sleep_time = (step.offset_time - last_offset_time) * sleepfactor
            print '  Sleeping for', sleep_time, 'ms'
            time.sleep(float(sleep_time) / 1000)
            step.execute(self)
            last_offset_time = step.offset_time

    @classmethod
    def record(cls, d, remote_d, url, screen_size, path, diffcolor, sleepfactor, save_diff):
        print 'Begin record'
        try:
            os.makedirs(path)
        except:
            pass
        test = Test(screen_size)
        run = TestRun(test, path, url, d, TestRunModes.RECORD, diffcolor, save_diff)
        d.set_window_size(*screen_size)
        navigate(d, url)
        start_time = d.execute_script('return +new Date();')
        d.execute_script('''
(function() {
var events = [];
window.addEventListener('click', function (e) { events.push([+new Date(), 'click', [e.clientX, e.clientY]]); }, true);
window.addEventListener('keyup', function (e) { events.push([+new Date(), 'keyup', String.fromCharCode(e.keyCode)]); }, true);
window._getHuxleyEvents = function() { return events; };
})();
''')
        steps = []
        while True:
            if len(raw_input("Press enter to take a screenshot, or type Q+enter if you're done\n")) > 0:
                break
            screenshot_step = ScreenshotTestStep(d.execute_script('return Date.now();') - start_time, run, len(steps))
            run.d.save_screenshot(screenshot_step.get_path(run))
            steps.append(screenshot_step)
            print len(steps), 'screenshots taken'

        # now capture the events
        try:
            events = d.execute_script('return window._getHuxleyEvents();')
        except:
            raise TestError(
                'Could not call window._getHuxleyEvents(). ' +
                'This usually means you navigated to a new page, which is currently unsupported.'
            )
        for (timestamp, type, params) in events:
            if type == 'click':
                steps.append(ClickTestStep(timestamp - start_time, params))
            elif type == 'keyup':
                steps.append(KeyTestStep(timestamp - start_time, params))

        steps.sort(key=operator.attrgetter('offset_time'))

        test.steps = steps

        print
        raw_input(
            'Up next, we\'ll re-run your actions to generate screenshots ' +
            'to ensure they are pixel-perfect when running automated. ' +
            'Press enter to start.'
        )
        print
        cls.rerecord(test, path, url, remote_d, sleepfactor, diffcolor, save_diff)

        return test

