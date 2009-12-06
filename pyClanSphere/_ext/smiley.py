#!/usr/bin/env python -u

"""
smiley.py from http://www.la-la.com
As amended by Michael Foord

This version is edited to work with the Voidspace Guestbook
http://www.voidspace.org.uk/python/guestbook.html
"""

##    smiley.py
##    v0.1.0, 2005\03\31
##    A smiley library handler for phpbb style smiley paks
##    Copyright (C) 2005  Mark Andrews
##    E-mail : mark AT la-la DOT com
##    Website: http://la-la.com
##
##    For Kim for bringing me so much laughter and smiles
##
##    This software is licensed under the terms of the BSD license.
##    Basically you're free to copy, modify, distribute and relicense it,
##    So long as you keep a copy of the license with it.
##
##    Requires path.py from http://www.jorendorff.com/articles/python/path/

import re
from path import path
repak = re.compile(r'^(.*?)=\+:(.*?)=\+:(.*)')
resmile = re.compile(r'.*(:[^:]+:).*')
reno = re.compile(r'.*(<code|<pre)(\s.*?)?>.*')
reyes = re.compile(r'.*(</code>|</pre>).*')

class lib(object):
    def __init__(self, source=None, url=None, replace=False, safe=False):
        self.debug = 1
        self.sources=[]
        self.clear()
        if source:
            self.load(source, url, replace)
    
    def clear(self):
        self.smilies={}
        
    def load(self, source, url=None, replace=False, safe=False):
        """Loads phpbb style smiley paks from directory source. Image locations are prepended with url.
        With replace set to true, later smilies with same key will overwrite original.
        With safe set to true, only smilies with :smile: style keys will be included."""
        p = path(source)
        if self.debug > 2:
            print "source: %s, url: %s" % (source,url)
        if url == None:
            url = '/'
        elif url[-1] != '/':
            #above expression was written clumsily as: url[len(url)-1]
            url = url + '/'
        else:
            pass
        for fn in p.files('*.pak'):
            f = fn.open()
            for l in f:
                s = repak.match(l)
                if s:
                    key = s.groups(0)[2].strip()
                    if not safe or resmile.match(key):
                        if replace or not self.smilies.has_key(key):
                            self.smilies[key]=[url + s.groups(0)[0],s.groups(0)[1]]
                            if self.debug > 2:
                                print "%s: %s" % (key,self.smilies[key])
            f.close()
        self.sources.append(source)

    def parsetoken(self, t, nest=0):
        """recursive routine to replace :smile: tags"""
        r = resmile.match(t)
        if r:
            rn = r.groups(0)[0]
            if self.smilies.has_key(rn):
                rt = self.get_tag(self.smilies[rn][0], self.smilies[rn][1])
                t = re.sub(re.escape(rn), rt, t)
                t = self.parsetoken(t, nest)
            else:
                # not a known smiley, hide and try again
                nest = nest + 1
                rt = 'smileynest' + str(nest)
                t = re.sub(re.escape(rn[:len(rn)-2]), rt, t)
                t = self.parsetoken(t, nest)
                t = re.sub(rt, rn[:len(rn)-2], t)
        return t

    def makehappy(self, text):
        """Replaces all smiley codes in text with their image links and returns the updated text.
        A :-) style smilie next to other characters will not be replaced. :smile: ones will.
        Tabs and multiple spaces will be replaced by a single space.
        <pre></pre> and <code></code> sections are ignored, though the start and end tags should be on
        individual lines for clean results."""       
        buf = text.split('\n')
        text = ''
        process = True
        for l in buf:
            tokens = l.split(' ')
            if reno.match(l):
                process = False
            if reyes.match(l):
                process = True
            if process:
                tl = ''
                for t in tokens:
                    if self.smilies.has_key(t):
                        t = self.get_tag(self.smilies[t][0], self.smilies[t][1])
                    else:
                        t = self.parsetoken(t)
                    tl = tl + ' ' + t
                text = text + tl[1:] + '\n' # leading space gained on first token
            else:
                # pass code and pre sections unmodified
                text = text + l
        return text
    
    def get_tag(self, image, alt):
        """Override this if you want to add class information etc to the image tags"""
        tag = '<img src="' + image + '" alt="' + alt + '" />'
        return tag
    
    def get_insert(self, key):
        """Override this if you want to add class information etc to the insert links"""
        t = self.get_tag(self.smilies[key][0], self.smilies[key][1])
        if not key[0] == key[-1] == ':':
            key = ' %s ' % key
        return """<a href="#" onClick="return insert('""" + key + """')">""" + t + '</a>'

    def get_panel(self, textarea="textarea"):
        """Returns HTML to display current smiley set with clickable Javascript links to insert into form.textarea"""
        panel = r"""<script language="JavaScript" type="text/javascript">
<!--
function insert(myValue) {
myField = document.getElementById('""" + textarea + r"""');
//IE support
if (document.selection) {
myField.focus();
sel = document.selection.createRange();
sel.text = myValue;
}
//MOZILLA/NETSCAPE support
else if (myField.selectionStart || myField.selectionStart == '0') {
var startPos = myField.selectionStart;
var endPos = myField.selectionEnd;
myField.value = myField.value.substring(0, startPos)
+ myValue
+ myField.value.substring(endPos, myField.value.length);
} else {
myField.value += myValue;
}
myField.focus();
return false;
} 
document.getElementById('""" + textarea + r"""').focus();//-->
</script>
"""
        for s in self.smilies.keys():
            panel = panel + self.get_insert(s) + '\n'
        return panel
