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

import ConfigParser
import glob
import os
import sys

import plac

from huxley.main import main as huxleymain

class ExitCodes(object):
    OK = 0
    NEW_SCREENSHOTS = 1
    ERROR = 2

LOCAL_WEBDRIVER_URL = os.environ.get('HUXLEY_WEBDRIVER_LOCAL', 'http://localhost:4444/wd/hub')
REMOTE_WEBDRIVER_URL = os.environ.get('HUXLEY_WEBDRIVER_REMOTE', 'http://localhost:4444/wd/hub')

@plac.annotations(
    names=plac.Annotation(
        'Test case name(s) to use, comma-separated',
    ),
    testfile=plac.Annotation(
        'Test file(s) to use',
        'option',
        'f',
        str,
        metavar='GLOB'
    ),
    record=plac.Annotation(
        'Record a new test',
        'flag',
        'r'
    ),
    playback_only=plac.Annotation(
        'Don\'t write new screenshots',
        'flag',
        'p'
    )
)
def _main(
    names=None,
    testfile='Huxleyfile',
    record=False,
    playback_only=False
):
    testfiles = glob.glob(testfile)
    if len(testfiles) == 0:
        print 'no Huxleyfile found'
        return ExitCodes.ERROR

    new_screenshots = False

    for file in testfiles:
        msg = 'Running Huxley file: ' + file
        print '-' * len(msg)
        print msg
        print '-' * len(msg)

        print
        config = ConfigParser.RawConfigParser(
            allow_no_value=True
        )
        config.read([file])
        for testname in config.sections():
            if names and (testname not in names):
                continue
            test_config = dict(config.items(testname))
            url = config.get(testname, 'url')
            default_filename = os.path.join(
                os.path.dirname(file),
                testname + '.huxley'
            )
            filename = test_config.get(
                'filename',
                default_filename
            )
            sleepfactor = float(test_config.get(
                'sleepfactor',
                1.0
            ))
            postdata = test_config.get(
                'postdata'
            )
            if record:
                r = huxleymain(
                    url,
                    filename,
                    postdata,
                    local=LOCAL_WEBDRIVER_URL,
                    remote=REMOTE_WEBDRIVER_URL,
                    record=True
                )
            else:
                r = huxleymain(
                    url,
                    filename,
                    postdata,
                    remote=REMOTE_WEBDRIVER_URL,
                    sleepfactor=sleepfactor,
                    autorerecord=not playback_only
                )
            new_screenshots = new_screenshots and (r != 0)

    if new_screenshots:
        return ExitCodes.NEW_SCREENSHOTS
    else:
        return ExitCodes.OK

def main():
    sys.exit(plac.call(_main))
