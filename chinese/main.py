# Modified by mentheosis@gmail.com 2020-02 for "Chinese-Text-Scanner" anki addon
#
# Copyright © 2017-2018 Joseph Lorimer <joseph@lorimer.me>
#
# This file is part of Chinese Support Redux.
#
# Chinese Support Redux is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Chinese Support Redux is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Chinese Support Redux.  If not, see <https://www.gnu.org/licenses/>.

from anki.hooks import addHook, wrap
from aqt import mw

from .singletons import dictionary, config
from .gui import load_menu, unload_menu

import jieba
jieba.setLogLevel(20)

if config['firstRun']:
    dictionary.create_indices()
    config['firstRun'] = False

def load():
    addHook('profileLoaded', load_menu)
    addHook('unloadProfile', config.save)
    addHook('unloadProfile', dictionary.conn.close)
    addHook('unloadProfile', unload_menu)
