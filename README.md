# Chinese Text Scanner
This will scan a text file, find any chinese words that contain new characters not already in the provided anki collection, and then produce an .apkg file which can be imported into anki. The import file will contain notes for all the new words, including tone colors and audio files powered by the chinese-support-redux project.

# Usage:
1. Install the addon and restart anki (refer to https://ankiweb.net/shared/info/2121493325)
2. TextScan will be added to the anki menu. Go there to open the scan dialog
3. The scan will produce a .apkg file which includes fully detailed notes, but it does not contain detailed card templates
4. In anki, select the imported notes and choose "change note type" to the port the new notes into your existing note types to utilize your existing card templates.

# Dev Mode:
Here's an easy way to get started deving:
1. Clone this, then create a symlink from anki's addon folder to the /chinese directory here
2. Set dev_mode to true in the textScanner config section
3. You'll need to restart Anki for the setting to take effect. You should notice the menu header gets a "_dev" appelation and a new menu item to probe the sqlite db. Tip: 'master' is a shortcut for 'select * from sqlite_master'

# Testing:
1. `make test`

# Building:
1. (optional) Add any new packages you want to use into requirements-minimal.txt
1. `make build` - creates temporary virtualenv and grabs any dependencies we need

# Package up a new zip file to publish:
1. Put the version you want in `chinese/_version.py`
2. Check the current version with `make version`
2. `make package` - this builds everything, creates a new zip file in build/ dir
4. The zip file will be put in build/


Based on [Chinese-Support-Redux](https://github.com/luoliyan/chinese-support-redux) by Joseph Lorimer which is based on the Chinese Support add-on by Thomas TEMPÉ and many others.

![Screenshot #1](https://raw.githubusercontent.com/mentheosis/anki-scanner-chinese-redux/master/screenshots/text-scanner.png)

![Screenshot #2](https://raw.githubusercontent.com/mentheosis/anki-scanner-chinese-redux/master/screenshots/add-card.png)
