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

import os
import threading

from huxley.consts import TestRunModes
from huxley.errors import TestError
from huxley.images import images_identical, image_diff

# Since we want consistent focus screenshots we steal focus
# when taking screenshots. To avoid races we lock during this
# process.
SCREENSHOT_LOCK = threading.RLock()

class TestStep(object):
    def __init__(self, offset_time):
        self.offset_time = offset_time

    def execute(self, run):
        raise NotImplementedError


class ClickTestStep(TestStep):
    CLICK_ID = '_huxleyClick'

    def __init__(self, offset_time, pos):
        super(ClickTestStep, self).__init__(offset_time)
        self.pos = pos

    def execute(self, run):
        print '  Clicking', self.pos
        # Work around multiple bugs in WebDriver's implementation of click()
        run.d.execute_script(
            'document.elementFromPoint(%d, %d).click();' % (self.pos[0], self.pos[1])
        )
        run.d.execute_script(
            'document.elementFromPoint(%d, %d).focus();' % (self.pos[0], self.pos[1])
        )


class KeyTestStep(TestStep):
    KEY_ID = '_huxleyKey'

    def __init__(self, offset_time, key):
        super(KeyTestStep, self).__init__(offset_time)
        self.key = key

    def execute(self, run):
        print '  Typing', self.key
        id = run.d.execute_script('return document.activeElement.id;')
        if id is None or id == '':
            run.d.execute_script(
                'document.activeElement.id = %r;' % self.KEY_ID
            )
            id = self.KEY_ID
        run.d.find_element_by_id(id).send_keys(self.key.lower())


class ScreenshotTestStep(TestStep):
    def __init__(self, offset_time, run, index):
        super(ScreenshotTestStep, self).__init__(offset_time)
        self.index = index

    def get_path(self, run):
        return os.path.join(run.path, 'screenshot' + str(self.index) + '.png')

    def execute(self, run):
        print '  Taking screenshot', self.index
        original = self.get_path(run)
        new = os.path.join(run.path, 'last.png')

        with SCREENSHOT_LOCK:
            # Steal focus for a consistent screenshot
            run.d.switch_to_window(run.d.window_handles[0])
            if run.mode == TestRunModes.RERECORD:
                run.d.save_screenshot(original)
            else:
                run.d.save_screenshot(new)
                try:
                    if not images_identical(original, new):
                        if run.save_diff:
                            diffpath = os.path.join(run.path, 'diff.png')
                            diff = image_diff(original, new, diffpath, run.diffcolor)
                            raise TestError(
                                ('Screenshot %s was different; compare %s with %s. See %s ' +
                                 'for the comparison. diff=%r') % (
                                    self.index, original, new, diffpath, diff
                                )
                            )
                        else:
                            raise TestError('Screenshot %s was different.' % self.index)
                finally:
                    if not run.save_diff:
                        os.unlink(new)
