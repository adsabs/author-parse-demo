# -*- coding: utf-8 -*-


import re
import sys
import unicodedata
from simplejson import dumps
from unidecode import unidecode
from author_tokenizer import tokenizer

import flask
app = flask.Flask(__name__)

def normalize(s):
    s = s.strip()
    s = re.sub('\s+', ' ', s)
    pattern = re.compile(r'[^\w,\-\']', re.U)
    s = re.sub(pattern, ' ', s)
    return s.upper()

mappings = {
    u'\u0308': 'E',
    u'\u030a': 'A',
    u'\xf8': 'OE',
    u'\u030c': 'H'
}

def synonyms(orig):
    syn = [orig, unidecode(orig)]
    translit = unicodedata.normalize('NFD', orig)
    for k,v in mappings.items():
        if translit.find(k) != -1:
            translit = translit.replace(k, v)
    if translit not in syn:
        syn.append(translit)
    return syn

def get_variations(orig):
    variations = [orig]
    parsed = tokenizer.ads_parse_author_name(orig)
    return parsed
    
@app.route('/')
def author_form():
    return flask.render_template('form.html')

@app.route('/index')
def author_index():
    results = []
    author = flask.request.args.get('author')
    results.append({ 'section': 'Original', 'results': [author] })
    normalized = normalize(author)
    results.append({ 'section': 'Normalized', 'results': [normalized] })
    syn = synonyms(normalized)
    results.append({ 'section': 'Generated Synonym Group', 'results': syn })
    results.append({ 'section': 'Indexed', 'results': [normalized] })
    return flask.jsonify(result=results)

@app.route('/query')
def author_query():
    results = []
    author = flask.request.args.get('author')
    results.append({ 'section': 'Original', 'results': [author] })
    normalized = normalize(author)
    results.append({ 'section': 'Normalized', 'results': [normalized] })
    variations = get_variations(normalized)
    results.append({ 'section': 'Variations', 'results': [variations] })
    return flask.jsonify(result=results)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)

