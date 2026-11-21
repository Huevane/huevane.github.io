#!/usr/bin/env python3
"""Check every classical quote on index.html against the original texts.

For each entry in tools/quotes.json:
  1. the quote must occur in the Kanripo text it cites (main text or commentary layer,
     punctuation ignored, base-edition characters as is);
  2. the same string must appear on index.html.

Texts come from the Kanripo repositories on GitHub (https://github.com/kanripo), master branch.
They are downloaded once into a cache directory (default: ./.kanripo-cache, override with KR_CACHE)
using the GitHub CLI (`gh api`), which must be logged in.

usage: python3 -I tools/verify_quotes.py
exit status 1 if any quote fails.
"""
import base64, functools, glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
CACHE = os.environ.get('KR_CACHE') or os.path.join(ROOT, '.kanripo-cache')


def fetch(krid):
    d = os.path.join(CACHE, krid)
    if glob.glob(os.path.join(d, '*.txt')):
        return d
    os.makedirs(d, exist_ok=True)
    names = subprocess.run(['gh', 'api', f'repos/kanripo/{krid}/contents?ref=master', '--jq',
                            '.[]|select(.name|endswith(".txt"))|.name'],
                           capture_output=True, text=True, check=True).stdout.split()
    for n in names:
        raw = subprocess.run(['gh', 'api', f'repos/kanripo/{krid}/contents/{n}?ref=master', '--jq', '.content'],
                             capture_output=True, text=True, check=True).stdout
        open(os.path.join(d, n), 'wb').write(base64.b64decode(raw))
    return d


@functools.lru_cache(None)
def raw_text(krid):
    out = []
    for f in sorted(glob.glob(os.path.join(fetch(krid), '*.txt'))):
        s = open(f, encoding='utf-8', errors='ignore').read()
        s = re.sub(r'^#.*$', '', s, flags=re.M).replace('¶', '').replace('\n', '')
        s = re.sub(r'<pb:[^>]+>', '', s)
        s = re.sub(r'&KR\d+;', '〓', s)
        out.append(s)
    return ''.join(out)


def all_text(krid):   # main text + commentary, in reading order
    return re.sub(r'[()/]', '', raw_text(krid))


def main_text(krid):  # commentary in ( ) removed
    return re.sub(r'\([^()]*\)', '', raw_text(krid))


PUNCT = re.compile(r'[，。、；：！？「」『』《》〈〉·\s　…—]')
bare = lambda s: PUNCT.sub('', s)

Q = json.load(open(os.path.join(HERE, 'quotes.json'), encoding='utf-8'))['quotes']
html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
page = re.sub(r'<[^>]+>', '', html)
# main-text view: drop 雙行夾注 spans so a note inside a sentence does not break the match
page_main = re.sub(r'<span class="zhu"[^>]*>(?:\s*<span class="r">[^<]*</span>\s*)+</span>', '', html)
page_main = re.sub(r'<[^>]+>', '', page_main)

fail = 0
for q in Q:
    src = main_text(q['source']) if q['layer'] == 'main' else all_text(q['source'])
    s_ok = bare(q['text']) in bare(src)
    view = page_main if q['layer'] == 'main' else page
    p_ok = q['text'] in view or bare(q['text']) in bare(view) or bare(q['text']) in bare(page)
    if not (s_ok and p_ok):
        fail += 1
    print(f"{'OK ' if s_ok and p_ok else 'ERR'} {q['id']:<10} source={'ok' if s_ok else 'MISSING':<7} "
          f"page={'ok' if p_ok else 'MISSING':<7} {q['text']}  {q['cite']}")
print(f"\n{len(Q) - fail}/{len(Q)} verified")
sys.exit(1 if fail else 0)
