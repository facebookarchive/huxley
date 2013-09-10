#!/bin/env python
# -*- coding: utf-8 -*-
#Filename:  huxleytest.py
#Date:      2013-08-29

import os
import sys
import glob
import json
import urlparse
import ConfigParser

from huxley.errors import TestError
from huxley.main import main as huxleymain

# Python unittest integration. These fail when the screen shots change, and they
# will pass the next time since they diff by last run result screen shots.

DEFAULTS = json.loads(os.environ.get('HUXLEY_DEFAULTS', 'null'))

class HuxleyConfig(object):
    """only support one section

    just for Huxleyfile.conf

    [toggle]
    url=http://192.168.159.131:8000/toggle.html
    filename=toggle.huxley
    sleepfactor=1.0
    postdata=null
    screensize=1024x768

    """

    def __init__(self, config_file ='Huxleyfile.conf'):
        self._config_file = config_file

        config = ConfigParser.SafeConfigParser(
            defaults=DEFAULTS,
            allow_no_value=True
        )
        config.read(self._config_file)
        testname = config.sections()[0]

        test_config = dict(config.items(testname))
        self._url = config.get(testname, 'url')

        default_filename = os.path.join(
            os.path.dirname(self._config_file),
            testname + '.huxley'
        )
        self._run_dir = test_config.get(
            'filename',
            default_filename
        )
        self._sleepfactor = float(test_config.get(
            'sleepfactor',
            1.0
        ))
        self._postdata = test_config.get(
            'postdata'
        )
        self._screensize = test_config.get(
            'screensize',
            '1024x768'
        )

    @property
    def url(self):
        return  self._url

    @property
    def run_dir(self):
        return  self._run_dir

    @property
    def sleepfactor(self):
        return  self._sleepfactor

    @property
    def postdata(self):
        return  self._postdata

    @property
    def screensize(self):
        return  self._screensize


class HuxleyTestCase(object):
    """ HuxleyTest base class

        you can inherit HuxleyTestCase for your own ui test
        by default,you just do like:
            class OwnHuxleyTestCase(unittest.TestCase, HuxleyTestCase):
                pass

        if you want to do something before or end testing,just do like:
            class OwnHuxleyTestCase(unittest.TestCase, HuxleyTestCase):

                def setUp(self):
                    ...
                def tearDown(self):
                    ...

        if you want to control test yourself, just overwrite test_huxley_base() function:
            class OwnHuxleyTestCase(unittest,TestCase, HuxleyTestCase):

                def test_huxley_base(self):
                    ...

    """
    recording = False
    playback_only = False
    local_webdriver_url = os.environ.get('HUXLEY_WEBDRIVER_LOCAL', 'http://192.168.159.130:4444/wd/hub')
    remote_webdriver_url = os.environ.get('HUXLEY_WEBDRIVER_REMOTE', 'http://192.168.159.130:4444/wd/hub')
    test_confirm_url = os.environ.get('HUXLEYVIEW_URL', 'http://192.168.159.131:9999/huxley/')

    def test_huxley_base(self):
        test_error_list = []
        i_dir = os.path.dirname(sys.modules[self.__class__.__module__].__file__)
        msg = """
               # Okkkkkkkkkkkkkkkkk,Let'party------------------------
               #
               #                 _   /|          Running Huxley test:%s
               #                 │
               #                 \'o.O'
               #                 │In [3]:
               #                 =(___)=
               # │---------------------------------------------------
                                   U
              """ % os.path.basename(i_dir)
        print '\n'.join([line.strip() for line in msg.splitlines()])

        #foreach all dirs, run each test
        huxley_configs = glob.glob(os.path.join(i_dir, '*.conf'))
        if len(huxley_configs) > 1:
            raise ValueError('only support one conf file, current dir:%s has %d files'
                    % (i_dir, len(huxley_configs)))
        if len(huxley_configs) < 1:
            raise ValueError('None conf file' % (i_dir, len(huxley_configs)))
        config = HuxleyConfig(os.path.join(os.path.realpath(i_dir), os.path.basename(huxley_configs[0])))

        try:
            huxleymain(
                    url=config.url,
                    filename=config.run_dir,
                    postdata=config.postdata,
                    sleepfactor=config.sleepfactor,
                    screensize=config.screensize,
                    remote=self.remote_webdriver_url,
                    save_diff=True,
                    his_mode=True
                )
        except TestError, e:
            for ierror in e.errorlist:
                timestamp = ierror['timestamp'].strftime('%Y%m%d%H%M%S')
                errmsg = """
                           ------------------------------------------------------------------------------------------------
                             _____ ____  ____   ___  ____
                            | ____|  _ \|  _ \ / _ \|  _ \
                            |  _| | |_) | |_) | | | | |_) |
                            | |___|  _ <|  _ <| |_| |  _ <
                            |_____|_| \_\_| \_\\___/|_| \_\

                            Test_URL:%s
                            Errmsg:%s
                            Step:%s
                            Confirm URL:%s
                           ------------------------------------------------------------------------------------------------

                         """  % (config.url, ierror['error'], ierror['step'],
                                    urlparse.urljoin(self.test_confirm_url, os.path.join(str(item[0]), timestamp, timestamp)))
                print '\n'.join([line.strip() for line in errmsg.splitlines()])
                test_error_list.append(ierror)

        self.assertEqual(len(test_error_list), 0, 'New screenshots were taken and written. Please be sure to review and check in.')
