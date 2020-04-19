# Copyright © 2012 Roland Sieker <ospalh@gmail.com>
# Copyright © 2012 Thomas TEMPÉ <thomas.tempe@alysse.org>
# Copyright © 2017-2019 Joseph Lorimer <joseph@lorimer.me>
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

from collections import defaultdict
from json import dump, load
from os.path import dirname, exists, join, realpath

class ConfigManager:

    def __init__(self, externalMode=False):
        self.default_path = join(dirname(realpath(__file__)), 'config.json')
        self.saved_path = join(dirname(realpath(__file__)), 'config_saved.json')
        self.externalMode = externalMode
        if self.externalMode == False:
            from aqt import mw
            self.mw = mw
        with open(self.default_path, encoding='utf-8') as f:
            self.default_config = defaultdict(str, load(f))

    def ensure_defaults(self,target,defaults):
        defaulted = False
        for key in defaults["textScanner"]:
            if target["textScanner"].get(key) == None:
                target["textScanner"][key] = defaults["textScanner"][key]
                defaulted = True
        if defaulted == True:
            self.mw.addonManager.writeConfig(__name__, self.config)

    def refresh_config(self):
        if self.externalMode == False:
            self.config = self.mw.addonManager.getConfig(__name__)
            self.ensure_defaults(self.config, self.default_config)
        else:
            self.config = self.default_config
            if exists(saved_path):
                with open(saved_path, encoding='utf-8') as f:
                    config_saved = defaultdict(str, load(f))
                self.ensure_defaults(config_saved, self.default_config)
                self.config = config_saved

    def toString(self, printKey='textScanner'):
        str=""
        for item in self.config[printKey]:
            str = str+f"\n\n{item}: {self.config[printKey][item]['val']}"
        return str

    def __setitem__(self, key, value):
        self.config[key] = value
        self.mw.addonManager.writeConfig(__name__, self.config)

    def __getitem__(self, key):
        self.refresh_config()
        return self.config[key]

    def update(self, d):
        self.config.update(d)
        self.mw.addonManager.writeConfig(__name__, self.config)

    def save(self):
        if self.externalMode == False:
            self.mw.addonManager.writeConfig(__name__, self.config)
        else:
            with open(self.saved_path, 'w', encoding='utf-8') as f:
                dump(self.config, f)

    def get_fields(self, groups=None):
        self.refresh_config()
        if not groups:
            groups = list(self.config['fields'])
        fields = []
        for g in groups:
            if g in self.config['fields']:
                fields.extend(self.config['fields'][g])
        return fields
