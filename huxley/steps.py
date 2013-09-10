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
import re
import time
from datetime import datetime
from selenium.webdriver import ActionChains

from huxley.consts import TestRunModes, TestRunStartTime
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
        print '  Clicking', self.pos
        # Work around multiple bugs in WebDriver's implementation of click()
        run.d.execute_script(
            'document.elementFromPoint(%d, %d).click();' % (self.pos[0], self.pos[1])
        )

class DragAndDropTestStep(TestStep):
    CLICK_ID = '_huxleyDragAndDrop'

    def __init__(self, offset_time, mouse_down_pos, mouse_up_pos):
        super(DragAndDropTestStep, self).__init__(offset_time)
        self.mouse_down_pos = mouse_down_pos
        self.mouse_up_pos = mouse_up_pos

    def execute(self, run):
        print 'Drag and drop', self.mouse_down_pos, self.mouse_up_pos
        # Work around multiple bugs in WebDriver's implementation of drag and drop
        drag_and_drop = ActionChains(run.d)
        drag_and_drop.move_to_element_with_offset(run.d.find_element_by_xpath('//body'), 0, 0)\
                    .move_by_offset(self.mouse_down_pos[0], self.mouse_down_pos[1])\
                    .click_and_hold()\
                    .move_by_offset(self.mouse_up_pos[0]-self.mouse_down_pos[0], self.mouse_up_pos[1]-self.mouse_down_pos[1])\
                    .release().perform()

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

    def get_latest_path(self, run, run_time=None):
        """
            get latest path by run_time, if has none, return None.Support for history record mode

            for exp:
                          run_time                  run_time_path              latest_dir
            (first_run)   2013/01/01 10:00:00 ==>   run.path/20130101100000    run.path/None
            (second_run)  2013/01/02 10:00:00 ==>   run.path/20130102100000    run.path/20130101000000
            (third_run)   2013/01/03 10:00:00 ==>   run.path/20130103100000    run.path/20130102000000
            ...

            and after `third_run`, you call:
                ScreenshotTestStep().get_latest_path(run, datetime.strftime('%Y%m%d%H%M%S', '20130102110000'))
                you will get run.path/20130102100000/screenshot1.png
        """
        if not run_time:
            run_time = TestRunStartTime.get_start_time()
        history_run_folders_time = [
                datetime.strptime(item, '%Y%m%d%H%M%S') for item in os.listdir(run.path) if re.match('\d+', item)]
        history_run_folders_time = [item for item in history_run_folders_time if item]

        if not history_run_folders_time:
            return None
        latest_dir_time = history_run_folders_time[
            history_run_folders_time.index(min(history_run_folders_time, key=lambda x:(run_time-x).seconds))]

        return os.path.join(run.path, latest_dir_time.strftime('%Y%m%d%H%M%S'), 'screenshot' + str(self.index) + '.png')

    def create_run_path(self, run, run_time=None):
        """mkdir run_time, for history record mode, please refer to get_latest_path"""
        if not run_time:
            run_time = TestRunStartTime.get_start_time()
        run_dir_path = os.path.join(run.path, run_time.strftime('%Y%m%d%H%M%S'))
        if not os.path.exists(run_dir_path):
            os.makedirs(run_dir_path)
        return run_dir_path

    def execute(self, run):
        print '  Taking screenshot', self.index
        if run.mode & TestRunModes.HISRECORD:
            run_start_time = TestRunStartTime().get_start_time()
            original = self.get_latest_path(run, run_start_time)
            if not original:
                original = os.path.join(self.create_run_path(run, run_start_time), 'screenshot' + str(self.index) + '.png')
                new = original
            else:
                new = os.path.join(self.create_run_path(run, run_start_time), 'screenshot' + str(self.index) + '.png')
        else:
            original = self.get_path(run)
            new = os.path.join(run.path, 'last.png')

        if run.mode & TestRunModes.RERECORD:
            run.d.save_screenshot(original)
        else:
            run.d.save_screenshot(new)
            try:
                if not images_identical(original, new):
                    if run.save_diff:
                        diffpath = new.replace('.png', '') + '_diff.png'
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
                if (not run.save_diff) and not (run.mode & TestRunModes.HISRECORD):
                    os.unlink(new)
