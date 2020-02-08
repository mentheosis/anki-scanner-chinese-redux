# Chinese Text Scanner
This will scan a text file, find any chinese words that contain new characters not already in the provided anki collection, and then produce an .apkg file which can be imported into anki. The import file will contain notes for all the new words, including tone colors and audio files powered by the chinese-support-redux project.

# Usage:
1. Install the addon and restart anki (refer to https://ankiweb.net/shared/info/2121493325)
2. TextScan will be added to the anki menu. Go there to open the scan dialog
3. The scan will produce a .apkg file which includes fully detailed notes, but it does not contain detailed card templates
4. In anki, select the imported notes and choose "change note type" to the port the new notes into your existing note types to utilize your existing card templates.

Based on [Chinese-Support-Redux](https://github.com/luoliyan/chinese-support-redux) by Joseph Lorimer which is based on the Chinese Support add-on by Thomas TEMPÉ and many others.

![Screenshot #1](https://raw.githubusercontent.com/mentheosis/anki-scanner-chinese-redux/master/screenshots/text-scanner.png)

![Screenshot #2](https://raw.githubusercontent.com/mentheosis/anki-scanner-chinese-redux/master/screenshots/add-card.png)
