#!/bin/env python
# -*- coding: utf-8 -*-
#Filename:  login_handler.py
#Date:      2013-08-30

from selenium.common.exceptions import NoSuchElementException

def login_handle(d, url):
    """Custom your own login func

    before you visit url, you must use login_handle to login
    """
    try:
        d.get(url)
        d.find_element_by_id('id_username').send_keys('admin')
        d.find_element_by_id('id_password').send_keys('netis')
        d.find_element_by_xpath("//input[@type='submit']").click()
    except NoSuchElementException:
        pass

