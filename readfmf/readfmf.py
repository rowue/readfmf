# -*- coding: utf-8 -*-
import codecs
import numpy
import StringIO
import re

def preParseData(b):
    localVar = {'fmf-version':'1.1','coding':'utf-8',
                'delimiter':'\t'}
    commentChar = ';'
    mapping={
            'whitespace':None,
            'semicolon' :';'
            }

    if b.startswith(codecs.BOM_UTF8):
        b = b.lstrip(codecs.BOM_UTF8)
    if b[0] == ';' or b[0] == '#':
        commentChar = b[0]
        items =  [var.strip().split(':') 
                    for var in b.split('-*-')[1].split(';')]
        try:
            for key,value in items:
                stripkey = key.strip()
                localVar[stripkey]=value.strip()
                if mapping.has_key(localVar[stripkey].lower()):
                    localVar[stripkey] = mapping[localVar[stripkey].lower()]
        except ValueError,e:
            from sys import exit
            exit('%s\nPlease, check syntax of headline, presumably a key' +
                 ' and its value are not separated by a colon.' % e)
    d = unicode(b, localVar['coding'])
    dataExpr = re.compile(ur"^(\[\*data(?::\s*([^\]]*))?\]\r?\n)([^[]*)", 
                    re.MULTILINE | re.DOTALL)
    commentExpr = re.compile(ur"^%s.*"%commentChar, re.MULTILINE)
    d = re.sub(commentExpr, '', d)
    preParsedData = {}
    def preParseData(match):
        try:
            preParsedData[match.group(2)] = \
                numpy.loadtxt(StringIO.StringIO(match.group(3)),
                                    unpack=True,
                                    comments=commentChar,
                                    dtype='S',
                                    delimiter=localVar['delimiter'])
        except Exception, e:
            return match.group(0)
        return u""
    d = re.sub(dataExpr, preParseData, d)
    return preParsedData, d, str(localVar['fmf-version'])

def stream2config(stream):
    fmfstring = stream.read()
    preParsedData, d, FMFversion = preParseData(fmfstring)
    from configobj import ConfigObj,ConfigObjError
    class FMFConfigObj(ConfigObj):
        _keyword = re.compile(r'''^ # line start
            (\s*)                   # indentation
            (                       # keyword
                (?:".*?")|          # double quotes
                (?:'.*?')|          # 'single quotes
                (?:[^'":].*?)       # no quotes
            )
            \s*:\s*                 # divider
            (.*)                    # value (including list values and comments)
            $   # line end
            ''', re.VERBOSE)  #'
    try:
        config = FMFConfigObj(d.encode('utf-8').splitlines(), encoding='utf-8')
    except ConfigObjError,e:
        from sys import exit
        exit('%s\nPlease check the syntax of the FMF-file, in particular' % e +
             ' the correct usage of comments.')
    return config, preParsedData
