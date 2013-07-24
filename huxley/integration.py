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
import unittest
import sys

from huxley.main import main

# Python unittest integration. These fail when the screen shots change, and they
# will pass the next time since they write new ones.
class HuxleyTestCase(unittest.TestCase):
    recording = False
    playback_only = False
    local_webdriver_url = os.environ.get('HUXLEY_WEBDRIVER_LOCAL', 'http://localhost:4444/wd/hub')
    remote_webdriver_url = os.environ.get('HUXLEY_WEBDRIVER_REMOTE', 'http://localhost:4444/wd/hub')

    def huxley(self, filename, url, postdata=None, sleepfactor=1.0):
        msg = 'Running Huxley test: ' + os.path.basename(filename)
        print
        print '-' * len(msg)
        print msg
        print '-' * len(msg)
        if self.recording:
            r = main(
                url,
                filename,
                postdata,
                local=self.local_webdriver_url,
                remote=self.remote_webdriver_url,
                record=True
            )
        else:
            r = main(
                url,
                filename,
                postdata,
                remote=self.remote_webdriver_url,
                sleepfactor=sleepfactor,
                autorerecord=not self.playback_only
            )

        self.assertEqual(0, r, 'New screenshots were taken and written. Please be sure to review and check in.')


def unittest_main(module='__main__'):
    if len(sys.argv) > 1 and sys.argv[1] == 'record':
        # Create a new test by recording the user's browsing session
        HuxleyTestCase.recording = True
        del sys.argv[1]
    elif len(sys.argv) > 1 and sys.argv[1] == 'playback':
        # When running in a continuous test runner you may want the
        # tests to continue to fail (rather than re-recording new screen
        # shots) to indicate a commit that changed a screen shot but did
        # not rerecord. TODO: we may want to build in auto-retry functionality
        # and automatically back off the sleep factor.
        HuxleyTestCase.playback_only = True
        del sys.argv[1]
    # The default behavior is to play back the test and save new screen shots
    # if they change.

    unittest.main(module)
