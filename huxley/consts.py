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

from datetime import datetime

class TestRunModes(object):
    RECORD = 0x01
    RERECORD = 0x02
    PLAYBACK = 0x04
    HISRECORD = 0x08

class TestRunStartTime(object):
    _instance = None
    _start_time = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TestRunStartTime, cls).__new__(
                                cls, *args, **kwargs)
            cls._start_time = datetime.now()
        return cls._instance

    @classmethod
    def get_start_time(cls):
        return cls._start_time

