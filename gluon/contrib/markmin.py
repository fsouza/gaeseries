#!/usr/bin/env python                                                                                                        # created my Massimo Di Pierro
# license MIT/BSD/GPL
import re
import cgi    

__all__ = ['render']

__doc__ = """
# Markmin markup language

## What?

This is a new markup language that we call markmin, it is implemented in the ``render`` function in the ``markmin.py`` module. 

## Why?

We wanted a markup language with the following requirements:
- less than 100 lines of functional code
- easy to read
- secure
- support table, ul, ol, code
- support html5 video and audio elements
- can align images and resize them
- can specify class for tables and code elements
- can add anchors anywhere
- does not use _ for markup (since it creates odd behavior)
- automatically links urls
- fast 

(results depend on text but in average for text ~100K markmin is 30% faster than markdown, for text ~10K it is 10x faster)

## Where

[[download http://web2py.googlecode.com/hg/gluon/contrib/markmin.py]]

## Usage

``
>>> from markmin import render
>>> render('hello **world**')
'<p>hello <b>world</b></p>'

``:python

## Examples

### Bold, italic, code and links

--------------------------------------------------
**SOURCE**                 | **OUTPUT**
``**bold**``               | **bold** 
``''italic''``             | ''italic'' 
``!`!`verbatim`!`!``       | ``verbatim``
``http://google.com``      | http://google.com
``[[click me #myanchor]]`` | [[click me #myanchor]]
---------------------------------------------------

### More on links

The format is always ``[[title link]]``. Notice you can nest bold, italic and code inside the link title.

### Anchors [[myanchor]]

You can place an anchor anywhere in the text using the syntax ``[[name]]`` where ''name'' is the name of the anchor.
You can then link the anchor with [[link #myanchor]], i.e. ``[[link #myanchor]]``.

### Images

[[some image http://www.google.it/images/srpr/nav_logo13.png right 200px]]
This paragraph has an image aligned to the right with a width of 200px. Its is placed using the code
``[[some image http://www.google.it/images/srpr/nav_logo13.png right 200px]]``.

### Unordered Lists

``
- Dog
- Cat
- Mouse
``

is rendered as 
- Dog
- Cat
- Mouse 

Two new lines between items break the list in two lists.

### Ordered Lists

``
+ Dog
+ Cat
+ Mouse
``

is rendered as
+ Dog
+ Cat
+ Mouse


### Tables

Something like this
``
---------
0 | 0 | X
0 | X | 0
X | 0 | 0
-----:abc
``
is a table and is rendered as
---------
0 | 0 | X
0 | X | 0
X | 0 | 0
-----:abc
Four or more dashes delimit the table and | separates the columns.
The ``:abc`` at the end sets the class for the table and it is optional.

### Blockquote

A table with a single cell is rendered as a blockquote:

-----
Hello world
-----

### Code, ``<code>``, escaping and extra stuff

``
def test():
    return "this is Python code"
``:python

Optionally a ` inside a ``!`!`...`!`!`` block can be inserted escaped with !`!.
The ``:python`` after the markup is also optional. If present, by default, it is used to set the class of the <code> block.
The behavior can be overridden by passing an argument ``extra`` to the ``render`` function. For example:

``>>> render("!`!!`!aaa!`!!`!:custom",extra=dict(custom=lambda text: 'x'+text+'x'))``:python

generates

``'xaaax'``:python

(the ``!`!`...`!`!:custom`` block is rendered by the ``custom=lambda`` function passed to ``render``).


### Html5 support

Markmin also supports the <video> and <audio> html5 tags using the notation:
``
[[title link video]]
[[title link audio]]
``

### Caveats
``<ul/>``, ``<ol/>``, ``<code/>``, ``<table/>``, ``<blockquote/>``, ``<h1/>``, ..., ``<h6/>`` do not have ``<p>...</p>`` around them.

"""

META = 'META'
regex_newlines = re.compile('(\n\r)|(\r\n)')
regex_code = re.compile('('+META+')|(``(?P<t>.*?)``(:(?P<c>\w+))?)',re.S)
regex_maps = [
    (re.compile('[ \t\r]+\n'),'\n'),
    (re.compile('[ \t\r]+\n'),'\n'),
    (re.compile('\*\*(?P<t>\w+( +\w+)*)\*\*'),'<b>\g<t></b>'),
    (re.compile("''(?P<t>\w+( +\w+)*)''"),'<i>\g<t></i>'),
    (re.compile('^#{6} (?P<t>[^\n]+)',re.M),'\n\n<<h6>\g<t></h6>\n'),
    (re.compile('^#{5} (?P<t>[^\n]+)',re.M),'\n\n<<h5>\g<t></h5>\n'),
    (re.compile('^#{4} (?P<t>[^\n]+)',re.M),'\n\n<<h4>\g<t></h4>\n'),
    (re.compile('^#{3} (?P<t>[^\n]+)',re.M),'\n\n<<h3>\g<t></h3>\n'),
    (re.compile('^#{2} (?P<t>[^\n]+)',re.M),'\n\n<<h2>\g<t></h2>\n'),
    (re.compile('^#{1} (?P<t>[^\n]+)',re.M),'\n\n<<h1>\g<t></h1>\n'),
    (re.compile('^\- +(?P<t>.*)',re.M),'<<ul><li>\g<t></li></ul>'),
    (re.compile('^\+ +(?P<t>.*)',re.M),'<<ol><li>\g<t></li></ol>'),
    (re.compile('</ol>\n<<ol>'),''),
    (re.compile('</ul>\n<<ul>'),''),
    (re.compile('<<'),'\n\n<<'),
    (re.compile('\n\s+\n'),'\n\n')]
regex_table = re.compile('^\-{4,}\n(?P<t>.*?)\n\-{4,}(:(?P<c>\w+))?\n',re.M|re.S)
regex_anchor = re.compile('\[\[(?P<t>\w+)\]\]')
regex_image_width = re.compile('\[\[(?P<t>.*?) +(?P<k>\S+) +(?P<p>left|right|center) +(?P<w>\d+px)\]\]')
regex_image = re.compile('\[\[(?P<t>.*?) +(?P<k>\S+) +(?P<p>left|right|center)\]\]')
regex_video = re.compile('\[\[(?P<t>.*?) +(?P<k>\S+) +video\]\]')
regex_audio = re.compile('\[\[(?P<t>.*?) +(?P<k>\S+) +audio\]\]')
regex_link = re.compile('\[\[(?P<t>.*?) +(?P<k>\S+)\]\]')
regex_auto = re.compile('(?<!["\w])(?P<k>\w+://[\w\.\-\?&%]+)',re.M)

def render(text,extra={},allowed={},sep='p'):
    """
    Arguments:
    - text is the text to be processed
    - extra is a dict like extra=dict(custom=lambda value: value) that process custom code
      as in " ``this is custom code``:custom "
    - allowed is a dictionary of list of allowed classes like
      allowed = dict(code=('python','cpp','java'))
    - sep can be 'p' to separate text in <p>...</p>
      or can be 'br' to separate text using <br /> 


    >>> render('this is\\n# a section\\nparagraph')
    '<p>this is</p><h1>a section</h1><p>paragraph</p>'
    >>> render('this is\\n## a subsection\\nparagraph')
    '<p>this is</p><h2>a subsection</h2><p>paragraph</p>'
    >>> render('this is\\n### a subsubsection\\nparagraph')
    '<p>this is</p><h3>a subsubsection</h3><p>paragraph</p>'
    >>> render('**hello world**')
    '<p><b>hello world</b></p>'
    >>> render('``hello world``')
    '<code class="">hello world</code>'
    >>> render('``hello world``:python')
    '<code class="python">hello world</code>'
    >>> render('``\\nhello\\nworld\\n``:python')
    '<pre><code class="python">hello\\nworld</code></pre>'
    >>> render("''hello world''")
    '<p><i>hello world</i></p>'
    >>> render('** hello** **world**')
    '<p>** hello** <b>world</b></p>'

    >>> render('- this\\n- is\\n- a list\\n\\nand this\\n- is\\n- another')
    '<ul><li>this</li><li>is</li><li>a list</li></ul><p>and this</p><ul><li>is</li><li>another</li></ul>'

    >>> render('+ this\\n+ is\\n+ a list\\n\\nand this\\n+ is\\n+ another')
    '<ol><li>this</li><li>is</li><li>a list</li></ol><p>and this</p><ol><li>is</li><li>another</li></ol>'

    >>> render("----\\na | b\\nc | d\\n----\\n")
    '<table class=""><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr></table>'

    >>> render("----\\nhello world\\n----\\n")
    '<blockquote class="">hello world</blockquote>'

    >>> render('[[this is a link http://example.com]]')
    '<p><a href="http://example.com">this is a link</a></p>'

    >>> render('[[this is an image http://example.com left]]')    
    '<p><img src="http://example.com" alt="this is an image" align="left" /></p>'
    >>> render('[[this is an image http://example.com left 200px]]')
    '<p><img src="http://example.com" alt="this is an image" align="left" width="200px" /></p>'

    >>> render('[[this is an image http://example.com video]]')    
    '<p><video src="http://example.com" controls></video></p>'
    >>> render('[[this is an image http://example.com audio]]')    
    '<p><audio src="http://example.com" controls></audio></p>'

    >>> render('[[this is a **link** http://example.com]]')
    '<p><a href="http://example.com">this is a <b>link</b></a></p>'

    >>> render("``aaa``:custom",extra=dict(custom=lambda text: 'x'+text+'x'))
    'xaaax'
    """
    #############################################################
    # replace all blocks marked with ``...``:class with META
    # store them into segments they will be treated as code
    #############################################################
    segments, i = [], 0
    text = regex_newlines.sub('\n',text)
    while True:
        item = regex_code.search(text,i)
        if not item: break
        if item.group()==META:
            segments.append((None,None))
            text = text[:item.start()]+META+text[item.end():]
        else:
            c = item.group('c') or ''
            if 'code' in allowed and not c in allowed['code']: c = ''
            code = item.group('t').replace('!`!','`')
            segments.append((code,c))
            text = text[:item.start()]+META+text[item.end():]
        i=item.start()+3

    #############################################################
    # do h1,h2,h3,h4,h5,h6,b,i,ol,ul and normalize spaces
    #############################################################
    text = '\n'.join(t.strip() for t in text.split('\n'))
    text = cgi.escape(text)
    for regex, sub in regex_maps:
        text = regex.sub(sub,text)
 
    #############################################################
    # process tables and blockquotes
    #############################################################
    while True:
        item = regex_table.search(text)
        if not item: break
        c = item.group('c') or ''
        if 'table' in allowed and not c in allowed['table']: c = ''
        content = item.group('t')
        if ' | ' in content:
            rows = content.replace('\n','</td></tr><tr><td>').replace(' | ','</td><td>')
            text = text[:item.start()] + '<<table class="%s"><tr><td>'%c + rows + '</td></tr></table>' + text[item.end():]
        else:
            text = text[:item.start()] + '<<blockquote class="%s">'%c + content + '</blockquote>' + text[item.end():]

    #############################################################
    # deal with images, videos, audios and links
    #############################################################

    text = regex_anchor.sub('<span id="\g<t>"><span>', text)
    text = regex_image_width.sub('<img src="\g<k>" alt="\g<t>" align="\g<p>" width="\g<w>" />', text)
    text = regex_image.sub('<img src="\g<k>" alt="\g<t>" align="\g<p>" />', text)
    text = regex_video.sub('<video src="\g<k>" controls></video>', text)
    text = regex_audio.sub('<audio src="\g<k>" controls></audio>', text)
    text = regex_link.sub('<a href="\g<k>">\g<t></a>', text)
    text = regex_auto.sub('<a href="\g<k>">\g<k></a>', text)
    
    #############################################################
    # deal with paragraphs (trick <<ul, <<ol, <<table, <<h1, etc)
    # the << indicates that there should NOT be a new paragraph
    # META indicates a code block therefore no new paragraph
    #############################################################
    items = [item.strip() for item in text.split('\n\n')]
    if sep=='p':
        text = ''.join(p[:2]!='<<' and p!=META and '<p>%s</p>'%p or '%s'%p for p in items if p)
    elif sep=='br':
        text = '<br />'.join(items)

    #############################################################
    # finally get rid of <<
    #############################################################
    text=text.replace('<<','<')
    
    #############################################################
    # process all code text
    #############################################################
    parts = text.split(META)
    text = parts[0]
    for i,(code,b) in enumerate(segments):
        if code==None:
            html = META
        else:
            if b in extra:
                if code[0]=='\n' and code[-1]=='\n': code=code[1:-1]
                html = extra[b](code)
            elif code[0]=='\n' or code[-1]=='\n':
                html = '<pre><code class="%s">%s</code></pre>' % (b,cgi.escape(code))
            else:
                html = '<code class="%s">%s</code>' % (b,cgi.escape(code))
        text = text+html+parts[i+1]
    return text


if __name__ == '__main__':
    import sys
    import doctest
    if len(sys.argv)>1:
        open(sys.argv[1],'w').write('<html><body>'+render(__doc__)+'</body></html>')
    else:
        doctest.testmod()
