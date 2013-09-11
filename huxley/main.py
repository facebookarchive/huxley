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

import contextlib
import os
import json
import sys

import jsonpickle
import plac
from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException

from huxley.run import TestRun
from huxley.consts import TestRunStartTime
from huxley.errors import TestError

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
    url=plac.Annotation('URL to hit'),
    filename=plac.Annotation('Test file location'),
    postdata=plac.Annotation('File for POST data or - for stdin'),
    record=plac.Annotation('Record a test', 'flag', 'r', metavar='URL'),
    rerecord=plac.Annotation('Re-run the test but take new screenshots', 'flag', 'R'),
    sleepfactor=plac.Annotation('Sleep interval multiplier', 'option', 'f', float, metavar='FLOAT'),
    browser=plac.Annotation(
        'Browser to use, either firefox, chrome, phantomjs, ie or opera.', 'option', 'b', str, metavar='NAME'
    ),
    remote=plac.Annotation('Remote WebDriver to use', 'option', 'w', metavar='URL'),
    local=plac.Annotation('Local WebDriver URL to use', 'option', 'l', metavar='URL'),
    diffcolor=plac.Annotation('Diff color for errors (i.e. 0,255,0)', 'option', 'd', str, metavar='RGB'),
    screensize=plac.Annotation('Width and height for screen (i.e. 1024x768)', 'option', 's', metavar='SIZE'),
    autorerecord=plac.Annotation('Playback test and automatically rerecord if it fails', 'flag', 'a'),
    save_diff=plac.Annotation('Save information about failures as last.png and diff.png', 'flag', 'e'),
    his_mode=plac.Annotation('run in history mode, you will get all screenshot png by each time', 'flag', 'H')
)
def main(
        url,
        filename,
        postdata=None,
        record=False,
        rerecord=False,
        sleepfactor=1.0,
        browser='firefox',
        remote=None,
        local=None,
        diffcolor='0,255,0',
        screensize='1024x768',
        autorerecord=False,
        save_diff=False,
        his_mode=False):

    print "start time:%s..." % TestRunStartTime().get_start_time().strftime('%Y-%m-%d %H:%M:%S')

    if postdata:
        if postdata == '-':
            postdata = sys.stdin.read()
        else:
            with open(postdata, 'r') as f:
                postdata = json.loads(f.read())
    try:
        if remote:
            d = webdriver.Remote(remote, CAPABILITIES[browser])
        else:
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

    try:
        if record:
            if local:
                local_d = webdriver.Remote(local, CAPABILITIES[browser])
            else:
                local_d = d
            with contextlib.closing(local_d):
                with open(jsonfile, 'w') as f:
                    f.write(
                        jsonpickle.encode(
                            TestRun.record(local_d, d, (url, postdata), screensize, filename, diffcolor, sleepfactor, save_diff, his_mode)
                        )
                    )
            print 'Test recorded successfully'
            return 0
        elif rerecord:
            with open(jsonfile, 'r') as f:
                TestRun.rerecord(jsonpickle.decode(f.read()), filename, (url, postdata), d, sleepfactor, diffcolor, save_diff, his_mode)
                print 'Test rerecorded successfully'
                return 0
        elif autorerecord:
            with open(jsonfile, 'r') as f:
                test = jsonpickle.decode(f.read())
            try:
                print 'Running test to determine if we need to rerecord'
                TestRun.playback(test, filename, (url, postdata), d, sleepfactor, diffcolor, save_diff, his_mode)
                print 'Test played back successfully'
                return 0
            except TestError:
                print 'Test failed, rerecording...'
                TestRun.rerecord(test, filename, (url, postdata), d, sleepfactor, diffcolor, save_diff, his_mode)
                print 'Test rerecorded successfully'
                return 2
        else:
            with open(jsonfile, 'r') as f:
                TestRun.playback(jsonpickle.decode(f.read()), filename, (url, postdata), d, sleepfactor, diffcolor, save_diff, his_mode)
                print 'Test played back successfully'
                return 0
    finally:
        try:
            d.close()
        except UnexpectedAlertPresentException:
            print "auto accept alert"
            alert = d.switch_to_alert()
            alert.accept()

if __name__ == '__main__':
    sys.exit(plac.call(main))
