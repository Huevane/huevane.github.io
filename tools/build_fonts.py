#!/usr/bin/env python3
"""Subset Chiron Sung HK (Regular + Bold) to exactly the characters used on index.html.
Writes fonts/chiron-n.woff2, fonts/chiron-b.woff2, fonts/fonts.css, fonts/OFL.txt.
usage: python3 -I tools/build_fonts.py DIR_WITH_ChironSungHK-N.ttf_AND_-B.ttf
Source fonts: https://github.com/chiron-fonts/chiron-sung-hk (STATIC_TTF)."""
import sys, os, re, html
from fontTools import subset
from fontTools.ttLib import TTFont

src_dir = sys.argv[1]
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
page = open(os.path.join(root, 'index.html'), encoding='utf-8').read()
text = html.unescape(re.sub(r'<[^>]+>', ' ', page))
# always include CJK punctuation / vertical forms and digits that layout or canvas may draw
text += '，。、；：「」『』《》〈〉·－＋—…↓→０１２３４５６７８９ 0123456789#ABCDEFabcdef北東南西風'
chars = sorted({c for c in text if ord(c) > 0x20})
out = os.path.join(root, 'fonts'); os.makedirs(out, exist_ok=True)
for weight, fn in (('n', 'ChironSungHK-N.ttf'), ('b', 'ChironSungHK-B.ttf')):
    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.layout_features = ['vert', 'vrt2', 'locl', 'ccmp', 'kern', 'vkrn', 'palt', 'vpal', 'halt', 'vhal', 'liga']
    opts.name_IDs = ['*']; opts.name_languages = ['*']; opts.notdef_outline = True
    opts.hinting = False
    f = TTFont(os.path.join(src_dir, fn))
    s = subset.Subsetter(opts); s.populate(text=''.join(chars)); s.subset(f)
    dst = os.path.join(out, f'chiron-{weight}.woff2')
    f.flavor = 'woff2'; f.save(dst)
    cmap = f.getBestCmap(); miss = [c for c in chars if ord(c) not in cmap and not c.isspace()]
    print(f'{dst}: {os.path.getsize(dst)/1024:.0f} KB, {len(chars)} chars requested, missing: {"".join(miss) or "-"}')
open(os.path.join(out, 'fonts.css'), 'w').write(
'''/* Chiron Sung HK 昭源宋體, (c) 2021-2026 Tamcy, SIL Open Font License 1.1 (see OFL.txt).
   Subset to the characters on index.html by tools/build_fonts.py. */
@font-face{font-family:"Chiron Sung HK";src:url("chiron-n.woff2") format("woff2");font-weight:400;font-display:swap}
@font-face{font-family:"Chiron Sung HK B";src:url("chiron-b.woff2") format("woff2");font-weight:400;font-display:swap}
''')
lic = os.path.join(src_dir, 'LICENSE.md')
if os.path.exists(lic):
    open(os.path.join(out, 'OFL.txt'), 'w').write(open(lic, encoding='utf-8').read())
