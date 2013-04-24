# TODO: test with phantomjs
# TODO: support key events
# TODO: support multiple pages

import time
import os
import json
import contextlib
import math
import operator

from selenium import webdriver
import Image, ImageChops
import plac

def rmsdiff_2011(im1, im2, diff):
    "Calculate the root-mean-square difference between two images"
    h = diff.histogram()
    sq = (value*(idx**2) for idx, value in enumerate(h))
    sum_of_squares = sum(sq)
    rms = math.sqrt(sum_of_squares/float(im1.size[0] * im1.size[1]))
    return rms

def images_identical(path1, path2, rms):
    im1 = Image.open(path1)
    im2 = Image.open(path2)
    #return ImageChops.difference(im1, im2).getbbox() is not None
    diff = ImageChops.difference(im1, im2)

    if diff.getbbox() is None:
        return True
    else:
        return False
        return rmsdiff_2011(im1, im2, diff) < rms

def get_rms(path1, path2):
    im1 = Image.open(path1)
    im2 = Image.open(path2)
    return rmsdiff_2011(im1, im2, ImageChops.difference(im1, im2))

def do_record(driver, url, dest):
    # TODO: only clicks for now.
    try:
        os.makedirs(dest)
    except:
        pass
    driver.get(url)
    driver.execute_script('''
(function() {
var start = Date.now();
var events = [];
window.addEventListener('click', function (e) { events.push([Date.now(), e.target.id]); }, true);
window._getJonxEvents = function() { return [start, events]; };
})();
''')
    screenshots = []
    while True:
        i = raw_input('press enter to take a screenshot, anything else to exit ')
        if len(i) > 0:
            break
        # take a screen shot
        driver.save_screenshot(os.path.join(dest, 'screenshot' + str(len(screenshots)) + '.png'))
        screenshots.append(driver.execute_script('return Date.now();'))
    
    start,events = driver.execute_script('return window._getJonxEvents();')
    log = []

    ssi = ei = 0
    last_time = start

    while len(log) < len(screenshots) + len(events):
        if ssi >= len(screenshots):
            event = events[ei]
            log.append(['event', event[0] - last_time, 'click', event[1]])
            ei += 1
            last_time = event[0]
        elif ei >= len(events):
            screenshot = screenshots[ssi]
            log.append(['screenshot', screenshot - last_time])
            ssi += 1
            last_time = screenshot
        else:
            screenshot = screenshots[ssi]
            event = events[ei]
            if screenshot < event[0]:
                log.append(['screenshot', screenshot - last_time])
                ssi += 1
                last_time = screenshot
            else:
                log.append(['event', event[0] - last_time, 'click', event[1]])
                ei += 1
                last_time = event[0]
    json.dump({'url': url, 'thresh': 0, 'log': log}, open(os.path.join(dest, 'record.json'), 'w'))
    
    # after we record we must immediately re-record to figure out what the rms image threshold is (since screenshots sometimes
    # look slightly different)
    print 'Re-recording to calculate threshold'
    do_playback(driver, dest)
    

def do_playback(d, src, rerecord=False):
    record = json.load(open(os.path.join(src, 'record.json')))
    url = record['url']
    log = record['log']
    thresh = original_thresh = record['thresh']

    d.get(url)

    screenshots = 0

    for item in log:
        type = item[0]
        ts = item[1]
        print 'Sleeping for', ts, 'ms'
        time.sleep(float(ts) / 1000)
        last_ts = ts
        if type == 'event':
            print 'Clicking', item[3]
            d.find_element_by_id(item[3]).click()
        else:
            print 'Taking a screen shot'
            # screen shot
            original_path = os.path.join(src, 'screenshot' + str(screenshots) + '.png')
            last_path = os.path.join(src, 'last.png')
            if rerecord:
                d.save_screenshot(last_path)
                # figure out a new threshold
                thresh = max(thresh, get_rms(original_path, last_path))
                # move last to current
                os.rename(last_path, original_path)
            else:
                d.save_screenshot(last_path)
                # compare
                if not images_identical(original_path, last_path, thresh):
                    raise ValueError('Screenshot %d was different, compare it and last.png' % screenshots)
            screenshots += 1

    # rewrite the json since the threshold may have changed.
    if rerecord:
        if thresh != original_thresh:
            print 'Threshold adjusted from', original_thresh, 'to', thresh
        record['thresh'] = thresh
        json.dump(record, open(os.path.join(src, 'record.json'), 'w'))
        print 'Test recorded successfully'
    else:
        print 'Test passed successfully'

DRIVERS = {
    'firefox': webdriver.Firefox,
    'chrome': webdriver.Chrome,
    'phantomjs': webdriver.PhantomJS,
    'ie': webdriver.Ie,
    'opera': webdriver.Opera
}    

@plac.annotations(
    filename=plac.Annotation('Test file location'),
    record=plac.Annotation('URL to open for test recording', 'option', 'r', str, metavar='URL'),
    rerecord=plac.Annotation('Re-run the test but take new screenshots', 'flag', 'R'),
    browser=plac.Annotation('Browser to use, either firefox, chrome, phantomjs, ie or opera.', 'option', 'b', str, metavar='NAME'),
)
def main(filename, record='', rerecord=False, browser='firefox'):
    try:
        d = DRIVERS[browser]()
    except KeyError:
        raise ValueError(
            'Invalid browser %r; valid browsers are %r.' % (browser, DRIVERS.keys())
        )
    with contextlib.closing(d):
        if len(record) > 0:
            do_record(d, record, filename)
        else:
            do_playback(d, filename, rerecord)

if __name__ == '__main__':
    plac.call(main)
