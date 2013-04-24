# TODO: test with phantomjs
# TODO: support key events
# TODO: support multiple pages

import time
import os
import json
import contextlib

from selenium import webdriver
import Image, ImageChops
import plac

def images_identical(path1, path2):
    im1 = Image.open(path1)
    im2 = Image.open(path2)
    return ImageChops.difference(im1, im2).getbbox() is None    

def image_diff(path1, path2, outpath, diffcolor):
    im1 = Image.open(path1)
    im2 = Image.open(path2)
    pix1 = im1.load()
    pix2 = im2.load()
    
    if im1.mode != im2.mode:
        raise ValueError('Different pixel modes between %r and %r' % (path1, path2))
    if im1.size != im2.size:
        raise ValueError('Different dimensions between %r and %r' % (path1, path2))

    mode = im1.mode
    width,height = im1.size

    for y in xrange(height):
        for x in xrange(width):
            if pix1[x,y] != pix2[x,y]:
                changed = True
                if mode == '1':
                    value = 255
                elif mode == 'L':
                    value = 255
                elif mode == 'RGB':
                    value = diffcolor
                elif mode == 'RGBA':
                    value = diffcolor + (255,)
                elif mode == 'P':
                    raise NotImplementedError('TODO: look up nearest pallette color')
                else:
                    raise NotImplementedError('Unexpected PNG mode')
                pix2[x, y] = value
    im2.save(outpath)

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
        if len(raw_input("Press enter to take a screenshot, or type Q+enter if you're done\n")) > 0:
            break
        # take a screen shot
        driver.save_screenshot(os.path.join(dest, 'screenshot' + str(len(screenshots)) + '.png'))
        screenshots.append(driver.execute_script('return Date.now();'))
        print len(screenshots), 'screenshots taken'
    
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
    json.dump({'url': url, 'log': log}, open(os.path.join(dest, 'record.json'), 'w'))

    # Sadly WebDriver doesn't *actually* click links, so :active states don't work. There are two options:
    # 1. Remove RMS error and possibly mask differences
    # 2. Just re-record and make sure they review the screenshots.
    # We went with #2
    
    driver.get('about:blank')
    raw_input("Because of how WebDriver handles :hover and :active, we need to re-record the test to take new screen shots. Please pay attention and ensure it looks good as the test runs, or review the screen shots at the end. Press enter to continue.")
    do_playback(driver, dest, True, (0, 255, 0))
    print "Be sure to review the screen shots if you weren\'t watching, as they may not be exactly the same."
    print "Finally we'll rerun the test to make sure it works."
    do_playback(driver, dest, False, (0, 255, 0))
    

def do_playback(d, src, rerecord, diffcolor):
    record = json.load(open(os.path.join(src, 'record.json')))
    url = record['url']
    log = record['log']

    d.get(url)

    screenshots = 0

    for item in log:
        type = item[0]
        ts = item[1]
        print '  Sleeping for', ts, 'ms'
        time.sleep(float(ts) / 1000)
        last_ts = ts
        if type == 'event':
            print '  Clicking', item[3]
            d.find_element_by_id(item[3]).click()
        else:
            print '  Taking a screen shot'
            # screen shot
            original_path = os.path.join(src, 'screenshot' + str(screenshots) + '.png')
            last_path = os.path.join(src, 'last.png')
            diff_path = os.path.join(src, 'diff.png');
            if rerecord:
                d.save_screenshot(original_path)
            else:
                d.save_screenshot(last_path)
                # compare
                if not images_identical(original_path, last_path):
                    image_diff(original_path, last_path, diff_path, diffcolor)
                    raise ValueError('Screenshot %d was different, compare it and last.png. See diff.png for the diff.' % screenshots)
            screenshots += 1

    if rerecord:
        print 'Test recorded successfully'
    else:
        print 'Test passed successfully'

DRIVERS = {
    'firefox': webdriver.Firefox,
    'chrome': webdriver.Chrome,
    'ie': webdriver.Ie,
    'opera': webdriver.Opera
}    

@plac.annotations(
    filename=plac.Annotation('Test file location'),
    record=plac.Annotation('URL to open for test recording', 'option', 'r', str, metavar='URL'),
    rerecord=plac.Annotation('Re-run the test but take new screenshots', 'flag', 'R'),
    browser=plac.Annotation('Browser to use, either firefox, chrome, phantomjs, ie or opera.', 'option', 'b', str, metavar='NAME'),
    diffcolor=plac.Annotation('Diff color for errors (i.e. 0,255,0)', 'option', 'd', str, metavar='RGB')
)
def main(filename, record='', rerecord=False, browser='firefox', diffcolor='0,255,0'):
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
            diffcolor = tuple(int(x) for x in diffcolor.split(','))
            do_playback(d, filename, rerecord, diffcolor)

if __name__ == '__main__':
    plac.call(main)
