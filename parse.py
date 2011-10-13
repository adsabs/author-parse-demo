# -*- coding: utf-8 -*-

import re
import sys
import unicodedata
from simplejson import dumps
from unidecode import unidecode
from author_tokenizer import tokenizer

import flask
app = flask.Flask(__name__)

BASE_PATH = '/author_parse'
#BASE_PATH = ''

def normalize(s):
    if not s: return
    s = s.strip()
    s = re.sub('\s+', ' ', s)
    s = s.replace('.', '')
    pattern = re.compile(r'[^\w,\-\']', re.U)
    s = re.sub(pattern, ' ', s)
    return s.upper()

mappings = {
    u'\u0308': 'E',
    u'\u030a': 'A',
    u'\xf8': 'OE',
    u'\u030c': 'H'
}

def gen_synonyms(orig):
    syn = set()
    syn.add(orig)
    syn.add(unidecode(orig))
    translit = unicodedata.normalize('NFD', orig)
    for k,v in mappings.items():
        if translit.find(k) != -1:
            translit = translit.replace(k, v)
    syn.add(translit)
    if len(syn) > 1:
        return list(syn)
    else:
        return []

def get_variations(orig, curated_proc=False):
    variations = []
    parsed = tokenizer.ads_parse_author_name(orig)

    last = normalize(parsed.get('last'))
    first = normalize(parsed.get('first'))
    middle = normalize(parsed.get('middle'))
    prefix = normalize(parsed.get('prefix'))
    suffix = normalize(parsed.get('suffix'))
    print >>sys.stderr, "%s %s %s" % (last, first, middle)

    if parsed.keys() == ['last']:
        # all we got was last name
        variations.append(last + ",.*")
    else:
        variations.append(last + ",")

    if first:
        if middle:
            if len(first) > 1:
                variations.append(last + ", " + first)
                variations.append(last + ", " + first[0])
                if len(middle) > 1:
                    variations.append(last + ", " + first + " " + middle + r"\b.*")
                    variations.append(last + ", " + first + " " + middle[0] + ".*")
                elif len(middle) == 1:
                    variations.append(last + ", " + first[0] + " " + middle + ".*")
                    variations.append(last + ", " + first + " " + middle + ".*")
            else:
                variations.append(last + ", " + first + "\w*")
                if len(middle) > 1:
                    variations.append(last + ", " + first + "\w* " + middle[0] + ".*")
                    variations.append(last + ", " + first + "\w* " + middle + r"\b.*")
                elif len(middle) == 1:
                    variations.append(last + ", " + first + "\w* " + middle + r".*")
        else:
            #variations.append('g) ' +last + ", " + first)
            if len(first) > 1:
                variations.append(last + ", " + first + r"\b.*")
                variations.append(last + ", " + first[0])
                if curated_proc:
                    variations.append(last + ", " + first[0] + r".*")
                else:
                    variations.append(last + ", " + first[0] + r"\b.*")
            elif len(first) == 1:
                variations.append(last + ", " + first + ".*")

    variations.sort(key=len)
    variations.reverse()
    return variations
    
def proc_synonyms(orig):
    proc_syn = []
    orig = set(orig)
    for a in orig:
        targets = orig.copy()
        targets.remove(a)
        targets = [x.replace(',','\,') for x in targets]
        proc_syn.append(('<span class="key">%s</span> => ' % a) + ", ".join(['<span class="target">%s</span>' % x for x in targets]))
        targets = [x + r'\b.*' for x in targets]
        for key in get_variations(a, curated_proc=True):
            key = '<span class="key">%s</span>' % key
            proc_syn.append(key + " => " + ", ".join(['<span class="target">%s</span>' % x for x in targets]))
    return proc_syn

@app.route('/')
def author_form():
    return flask.render_template('form.html', base_path=BASE_PATH)

@app.route('/index')
def author_index():
    results = []
    author = flask.request.args.get('author')
    results.append({ 'section': 'original', 'names': [author] })
    normalized = normalize(author)
    results.append({ 'section': 'normalized', 'names': [normalized] })
    syn = gen_synonyms(normalized)
    results.append({ 'section': 'index-synonyms', 'names': syn })
    results.append({ 'section': 'indexed', 'names': [normalized] })
    return flask.jsonify(result=results)

@app.route('/query')
def author_query():
    results = []
    author = flask.request.args.get('author')
    results.append({ 'section': 'original', 'names': [author] })
    normalized = normalize(author)
    results.append({ 'section': 'normalized', 'names': [normalized] })
    variations = get_variations(normalized)
    results.append({ 'section': 'variations', 'names': variations })
    return flask.jsonify(result=results)

@app.route('/gen_synonyms')
def get_gen_synonyms():
    results = set()
    input = flask.request.args.get('author')
    orig = re.split(r'\s*;\s*', input)
    results.update(orig)
    for name in orig:
        results.update(gen_synonyms(name))
    results = list(results)
    results.sort(key=len)
    results.reverse()
    return flask.jsonify(result=results)

@app.route('/synonym')
def author_synonyms():
    results = []
    input = flask.request.args.get('author')
    orig_syn = [normalize(x) for x in re.split(r'\s*\n\s*', input)]
    results.append({ 'section': 'original', 'names': orig_syn })
    expanded_syn = set(orig_syn[:])
    for orig in orig_syn:
        expanded_syn.update(gen_synonyms(orig))
    expanded_syn = list(expanded_syn)
    results.append({ 'section': 'auto-gen synonyms', 'names': expanded_syn })
    proc_syn = proc_synonyms(expanded_syn)
    results.append({ 'section': 'processed', 'names': proc_syn })
    return flask.jsonify(result=results)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)

