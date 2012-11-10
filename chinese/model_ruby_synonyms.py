# -*- coding: utf-8 -*-
# 
# Copyright © 2012 Thomas Tempe <thomas.tempe@alysse.org>
# Copyright © 2012 Roland Sieker <ospalh@gmail.com>
#
# Original: Damien Elmes <anki@ichi2.net> (as japanese/model.py)
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#

import string

import anki.stdmodels

# List of fields
######################################################################

fields_list = ["Hanzi", "Meaning", "Hanzi2", "Hanzi3", "Hanzi4", "Notes and pictures"]

# Card templates
######################################################################

recognition_front = string.Template(u'''
{{#Hanzi$num}}
<div class=tags>{{Deck}} {{#Tags}} -- {{/Tags}}{{Tags}}</div>

<div class=question>
<span class=chinese>{{ruby_bottom_text:Hanzi$num}}</span>
</div>

{{/Hanzi$num}}
''')

recall_front = string.Template(u'''
{{#Hanzi$num}}
<div class=tags>{{Deck}} {{#Tags}} -- {{/Tags}}{{Tags}}</div>

<div class=question>
{{Meaning}}<br>
<span class=chinese>
{{hanzi_silhouette:Hanzi$num}}</span>
</div>

<div class=hint>{{hint_transcription:Hanzi$num}}</div>
<div class=context>{{hanzi_context:Hanzi$num}}</div>
{{#Notes and pictures}}<div class=note>{{Notes and pictures}}</div>{{/Notes and pictures}}

{{/Hanzi$num}}
''')

card_back = string.Template(u'''
<div class=tags>{{Deck}} {{#Tags}} -- {{/Tags}}{{Tags}}</div>
<div class=question>
<div class=meaning>{{Meaning}}</div>
<span class=chinese>
{{ruby:Hanzi$num}}</span>
</div>

<div class=chinese>
{{ruby:Hanzi1}}
{{#Hanzi2}} / {{/Hanzi2}}{{ruby:Hanzi2}}
{{#Hanzi3}} / {{/Hanzi3}}{{ruby:Hanzi3}}
{{#Hanzi4}} / {{/Hanzi4}}{{ruby:Hanzi4}}
</div>
{{#Notes and pictures}}<div class=note>{{Notes and pictures}}</div>{{/Notes and pictures}}
''')

# CSS styling
######################################################################

css_style = u'''
.card {
 font-family: arial;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
}
.chinese { font-size: 30px }
.win .chinese { font-family: "MS Mincho", "ＭＳ 明朝"; }
.mac .chinese { }
.linux .chinese { font-family: "Kochi Mincho", "東風明朝"; }
.mobile .chinese { font-family: "Hiragino Mincho ProN"; }
.question {background-color:PapayaWhip;border-style:dotted;border-width:1pt;margin-top:15pt;margin-bottom:30pt;padding-top:15px;padding-bottom:15px;}
.tags {color:gray;text-align:right;font-size:10pt;}
.note {color:gray;font-size:12pt;margin-top:20pt;}
.hint {font-size:12pt;}
.tone1 {color: red;}
.tone2 {color: orange;}
.tone3 {color: green;}
.tone4 {color: blue;}
.tone5 {color: gray;}
'''

# Add model for chinese word to Anki
######################################################################

def add_model_ruby_synonyms(col):
    mm = col.models
    m = mm.new("Chinese Ruby with synonyms")
    # Add fields
    for f in fields_list:
        fm = mm.newField(f)
        mm.addField(m, fm)
    for n in ["", "2", "3", "4"]:
        t = mm.newTemplate(u"Recognition"+n)
        t['qfmt'] = recognition_front.substitute(num=n)
        t['afmt'] = card_back.substitute(num=n)
        mm.addTemplate(m, t)
        t = mm.newTemplate(u"Recall"+n)
        t['qfmt'] = recall_front.substitute(num=n)
        t['afmt'] = card_back.substitute(num=n)
        mm.addTemplate(m, t)

    m['css'] += css_style
    m['addon'] = "Chinese Ruby"
    mm.add(m)
    # recognition card
    return m

anki.stdmodels.models.append(("Chinese Ruby with synonyms", add_model_ruby_synonyms))