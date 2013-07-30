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

## Tutorial

In `example/` you'll find a simple completed Huxley test. To start fram scratch, simply remove `toggle.huxley` and `Huxleyfile`.

### Motivation

In `example/webroot/toggle.html` you'll find a very simple JavaScript application that implements a toggle button. The goal of Huxley is to make creating an integration for this component effortless, and to make it easy to update the test when the UI changes.

### Step 1: host your app somewhere

For our example, simply `cd` to `example/webroot` and run `python -m SimpleHTTPServer` to start a basic server for our demo. In your app you may need to start up whatever framework you're using.

### Step 2: create a Huxleyfile

A Huxleyfile describes your test. Create one that looks like this:

```
[toggle]
url=http://localhost:8000/toggle.html
```

This creates a test named `toggle` that tests the URL `http://localhost:8000/toggle.html`.

### Step 2: record the test

Huxley makes writing tests easy because it simply records your browser session -- specifically mouse clicks and key presses on a single page -- and can replay them in an automated way. To do this you need to install [Selenium Server](http://docs.seleniumhq.org/download/) and start it. It's as easy as `java -jar selenium-server-standalone-XXX.jar`.

Then, run Huxley in record mode: `huxley --record`. Huxley will bring up a browser using Selenium. Press enter in the Huxley console to take a screen shot of the initial page load. Then toggle the button in the browser a few times. After every click, switch back to the Huxley console to take a screen shot. When you've tested all of the functionality you want to test, simply type `q` and then enter in the Huxley console to exit.

After confirming, Huxley will automatically record the test for you and save it to disk as `toggle.huxley`. Be sure to commit the `Huxleyfile` as well as `toggle.huxley` into your repository so you can track changes to them.

### Step 3: playback

Simply run the `huxley` command in the same directory as the `Huxleyfile` to be sure that your app still works.

### Step 4: update the test with new screen shots

You'll likely update the UI of the component a lot without changing its core functionality. Huxley can take new screen shots for you when this happens. Tweak the UI of the component in `toggle.html` somehow (maybe change the button color or something) and re-run `huxley`. It will warn you that the UI has changed and will automatically write new screen shots for you. If you run `huxley` again, the test will pass since the screen shots were updated.

The best part is, since the screen shots are checked into the repository, you can review the changes to the UI as part of the code review process if you'd like. At Instagram we have frontend engineers reviewing the JavaScript and designers reviewing the screenshots to ensure that they're pixel perfect.

### Step 5: run in CI mode

If you're using a continuous integration solution like [Jenkins](http://jenkins-ci.org/) you probably don't want to automatically rerecord screen shots on failure. Simply run `huxley --playback-only` to do this.

Additionally, you may find that you're dissatisfied with Huxley replaying your browsing session in real-time. You can speed it up (or slow it down) by editing your `Huxleyfile` to read:

```
[toggle]
url=http://localhost:8000/toggle.html
sleepfactor=0.5
```

This edit should cut the execution time in half.

## Best practices

Integration tests sometimes get a bad rap for testing too much at once. We've found that if you use integration tests correctly they can be just as effective and accurate as unit tests. Simply follow a few best practices:

* **Don't test a live app. Use mocking to make your components reliable instead.** If you hit your live app, failures in any number of places could trigger false failures in your UI tests. Instead of hitting a real URL in your app, **create a dedicated test URL** for Huxley to hit that uses mocking (and perhaps dependency injection) to isolate your UI component as much as possible. Huxley is completely unopinionated; use whatever tools you want to do this.
* **Test a small unit of functionality.** You should try to isolate your UI into modular components and test each one individually. Additionally, try to test one interaction per Huxley test so that when it fails, it's easy to tell exactly which interaction is problematic and it's faster to re-run it.
