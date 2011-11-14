# -*- coding: utf-8; -*-

# Copyright (c) 2010-2011, Rectorate of the University of Freiburg
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of the Freiburg Materials Research Center,
#   University of Freiburg nor the names of its contributors may be used to
#   endorse or promote products derived from this software without specific
#   prior written permission.
#
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
# OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
