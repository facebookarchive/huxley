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

from huxley.consts import TestRunModes
from huxley.errors import TestError
from huxley.images import images_identical, image_diff

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
        pos = self.pos
        print '  Clicking', pos
        # Work around multiple bugs in WebDriver's implementation of click()
        elementClicked = run.d.execute_script(
            'return document.elementFromPoint(%d, %d);' % (pos[0], pos[1])
        )
        run.d.execute_script(
            'document.elementFromPoint(%d, %d).click();' % (pos[0], pos[1])
        )
        # If clicking on an input, focus it
        if (elementClicked.tag_name == 'input' or
            elementClicked.tag_name == 'textarea' or
            elementClicked.tag_name == 'select'):
            run.d.execute_script(
                'document.elementFromPoint(%d, %d).focus();' % (pos[0], pos[1])
            )
        else:
            # unfocus to prevent accidental keypress into a random field
            run.d.execute_script(
                'document.activeElement.blur();'
            )



class KeyTestStep(TestStep):
    KEY_ID = '_huxleyKey'

    def __init__(self, offset_time, key):
        super(KeyTestStep, self).__init__(offset_time)
        self.key = key

    def execute(self, run):
        print '  Typing', self.key
        activeElement = run.d.execute_script(
            'return document.activeElement;'
        )
        if activeElement is not None:
            activeElement.send_keys(self.key.lower())


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
