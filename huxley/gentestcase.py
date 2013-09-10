# -*- coding: utf-8 -*-

import os
import errno

class GenTestCase(object):
    """auto gen unittest testcase

    for exp:
    -->GenTestCase('sherlock').gen_testcase_py()
       it'will create test_sherlock folder and test_sherlock/test_sherlock.py
    -->GenTestCase('sherlock').gen_conf()
       it'will create test_sherlock folder and test_sherlock/Huxleyfile.conf
    """

    def __init__(self, project_name):
        self._project_name = project_name
        self._project_path = 'test_' + self._project_name
        self._testcase_py_path = os.path.join(self._project_path, "test_%s.py" % self._project_name)
        self._conf_path = os.path.join(self._project_path, "Huxleyfile.conf")
        self._testcase_py_content = """
            # -*- coding: utf-8 -*-

            from unittest import TestCase
            from huxley.huxleytest import HuxleyTestCase

            class %sTestCase(TestCase, HuxleyTestCase):
                pass

            """ % self._project_name
        self._conf_content = """
            [%s]
            url=http://github.com/facebook/huxley

            """ % self._project_name

        #mkdir -p project_name
        try:
            os.makedirs(self._project_path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(self._project_path):
                pass
            else: raise

    def gen(self):
        self.gen_testcase_py()
        self.gen_conf()

    def gen_testcase_py(self):
        with open(self._testcase_py_path, 'w+') as fp:
            lines = [line[12:]+'\n' for line in self._testcase_py_content.splitlines() if line]
            fp.writelines(lines)

    def gen_conf(self):
        with open(self._conf_path, 'w+') as fp:
            lines = [line[12:]+'\n' for line in self._conf_content.splitlines() if line]
            fp.writelines(lines)
