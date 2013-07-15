# Huxley

*Watches you browse, takes screenshots, tells you when they change*

Huxley is a test-like system for catching **visual regressions** in Web applications. It was built by [Pete Hunt](http://github.com/petehunt/) with input from [Maykel Loomans](http://www.miekd.com/) at [Instagram](http://www.instagram.com/).

## What is the problem?

* UI tests are hard to write and are usually fragile.
* Automated testing can't tell you if something doesn't look right, so UI regressions may go undetected.
* Designers can't participate in the code review process even though reviewing the way the UI looks is just as important as reviewing the code that creates it.

## How does Huxley help me?

Huxley runs in two modes:

### Record mode

Using Selenium WebDriver, Huxley opens a page and records your actions. When you press enter in the Huxley terminal, Huxley will save a screenshot.

Testing a new flow is as simple as manually testing it once. Huxley will remember and re-run your "manual" test plan for you automatically.

### Playback mode

You should run Huxley in playback mode before submitting code for review and in continuous integration. Huxley will open the page and re-run your actions with WebDriver. It will take screenshots and compare them with the original screenshots. If they have changed, it will save the new screenshots and warn you that they have changed.

When screenshots have changed, those screenshot changes will show up in your commit. A designer can review them to be sure they're OK. And your continuous integration system can alert you if you forgot to run Huxley.

By default, Huxley will overwrite the old screenshots with new ones. That means you don't have to rewrite anything when your UI changes like you would with a traditional WebDriver test -- Huxley will just take a new screenshot for you and when it's checked in your test is updated!

## Getting started

See `example/` for an example. Note: you should be running selenium-server on localhost as well as run `python -m SimpleHTTPServer` from `example/` for it to work out-of-the-box. Then just run `python example.py` to run Huxley.