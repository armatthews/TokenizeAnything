#coding: utf8
import re
import sys
import argparse
import subprocess
import unicodedata

def utf8_normalize(stream):
  for line in stream:
    yield unicodedata.normalize('NFKC', line.decode('utf-8'))

def html_hex_entity(match):
  u = int(match.group(1), 16)
  return unichr(u)

def html_entity(match):
  u = int(match.group(1), 10)
  return unichr(u)

# TODO: Break up this megalithic function
def quote_norm(line):
  line = ' %s ' % line
  # Delete control characters:
  line = re.sub(ur'[\x00-\x1F]+', ' ', line)

  # PTB --> normal
  line = line.replace(ur'-LRB-', '(')
  line = line.replace(ur'-RRB-', ')')
  line = line.replace(ur'-LSB-', '[')
  line = line.replace(ur'-RSB-', ']')
  line = line.replace(ur'-LCB-', '{')
  line = line.replace(ur'-RCB-', '}')
  line = line.replace(ur' gon na ', ' gonna ')

  # Regularize named HTML/XML escapes:
  line = re.sub(ur'&\s*lt\s*;', '<', line, flags=re.IGNORECASE)     # HTML opening angle bracket
  line = re.sub(ur'&\s*gt\s*;', '>', line, flags=re.IGNORECASE)     # HTML closing angle bracket
  line = re.sub(ur'&\s*squot\s*;', '\'', line, flags=re.IGNORECASE) # HTML single quote
  line = re.sub(ur'&\s*quot\s*;', '"', line, flags=re.IGNORECASE)   # HTML double quote
  line = re.sub(ur'&\s*nbsp\s*;', ' ', line, flags=re.IGNORECASE)   # HTML non-breaking space
  line = re.sub(ur'&\s*apos\s*;', '\'', line, flags=re.IGNORECASE)  # HTML apostrophe
  line = re.sub(ur'&\s*amp\s*;', '&', line, flags=re.IGNORECASE)    # HTML ampersand (last)

  # Regularize known HTML numeric codes:
  line = re.sub(ur'&\s*#\s*160\s*;', ' ', line)
  line = re.sub(ur'&\s*#45\s*;\s*&\s*#45\s*;', '--', line)
  line = re.sub(ur'&\s*#45\s*;', '--', line)

  # Convert arbitrary hex or decimal HTML entities to actual characters:
  line = re.sub(ur'&\#x([0-9A-Fa-f]+);', html_hex_entity, line)
  line = re.sub(ur'&\#([0-9]+);', html_entity, line)

  # Regularlize spaces:
  zero_width_spaces = [u'\u00ad', # soft hyphen
                       u'\u200C'] # zero-width non-joiner
  line = re.sub('|'.join(zero_width_spaces), '', line)

  spaces = [u'\u00a0', # non-breaking space
            u'\u2009', # thin space
            u'\u2028', # "line separator"
            u'\u2029', # "paragraph separator"
            u'\u202a', # "left-to-right embedding"
            u'\u202b', # "right-to-left embedding" 
            u'\u202c', # "pop directional formatting"
            u'\u202d', # "left-to-right override"
            u'\u202e', # "right-to-left override"
            u'\u0085', # "next line"
            u'\ufffd', # "replacement character"
            u'\ufeff', # byte-order mark
            u'\ufdd3'] # "unicode non-character"
  line = re.sub('|'.join(spaces), ' ', line)

  # Convert other Windows 1252 characters to UTF-8
  line = line.replace(u'\u0080', u'\u20ac') # euro sign
  line = line.replace(u'\u0095', u'\u2022') # bullet
  line = line.replace(u'\u0099', u'\u2122') # trademark sign

  # Currency and measure conversions:
  line = re.sub(ur' (\d\d): (\d\d)', ur' \1:\2', line)
  line = line.replace(u'\u20a0', u' EUR ')
  line = line.replace(u'\u20ac', u' EUR ')
  line = line.replace(u'\u00a3', u' GBP ')
  line = re.sub(ur'(\W)([A-Z]+\$?)(\d*\.\d+|\d+)', ur'\1\2 \3', line) # AU$12.34
  line = re.sub(ur'(\W)(euro?)(\d*\.\d+|\d+)', ur'\1EUR \3', line, flags=re.IGNORECASE) # EUR12.34

  # Ridiculous double conversions, UTF8 -> Windows 1252 -> UTF8:
  line = line.replace(u'ï¿½c', u'--')                 # long dash
  line = line.replace(u'\u00e2\u20acoe', u'"')        # opening double quote
  line = line.replace(u'\u00e2\u20ac\u009c', u'"')    # opening double quote
  line = line.replace(u'\u00e2\u20ac\u009d', u'"')    # closing double quote
  line = line.replace(u'\u00e2\u20ac\u2122', u'\'')   # apostrophe
  line = line.replace(u'\u00e2\u20ac\u201c', u' -- ') # en dash?
  line = line.replace(u'\u00e2\u20ac\u201d', u' -- ') # em dash?

  line = line.replace(u'\u00e2\u0080\u0098', ur'\'') # single quote?
  line = line.replace(u'\u00e2\u0080\u0099', ur'\'') # single quote?
  line = line.replace(u'\u00e2\u0080\u009c', ur'"')  # double quote?
  line = line.replace(u'\u00e2\u0080\u009d', ur'"')  # double quote?
  line = line.replace(u'\u00c3\u009f', u'\u00df')    # esset
  line = line.replace(u'\u00c3\u0178', u'\u00df')    # esset
  line = line.replace(u'\u00c3\u00a4', u'\u00e4')    # a umlaut
  line = line.replace(u'\u00c3\u00b6', u'\u00f6')    # o umlaut
  line = line.replace(u'\u00c3\u00bc', u'\u00fc')    # u umlaut
  line = line.replace(u'\u00c3\u0084', u'\u00c4')    # A umlaut: create no C4s after this
  line = line.replace(u'\u00c3\u201e', u'\u00c4')    # A umlaut: create no C4s after this
  line = line.replace(u'\u00c3\u0096', u'\u00d6')    # O umlaut
  line = line.replace(u'\u00c3\u2013', u'\u00d6')    # O umlaut
  line = line.replace(u'\u00c3\u00bc', u'\u00dc')    # U umlaut
  line = line.replace(u'\u0080', u'\u20ac')           # euro sign
  line = line.replace(u'\u0095', u'\u2022')           # bullet
  line = line.replace(u'\u0099', u'\u2122')           # trademark sign

  # Regularize quotes:
  line = line.replace(u'ˇ', u'\'')      # caron
  line = line.replace(u'´', u'\'')      # acute accent
  line = line.replace(u'`', u'\'')      # grave accent
  line = line.replace(u'ˉ', u'\'')      # modified letter macron
  line = line.replace(u' ,,', u'"')     # ghetto low-99 quote
  line = line.replace(u'``', u'"')      # latex-style left quote
  line = line.replace(u'\'\'', u'"')    # latex-style right quote
  line = line.replace(u'\u300c', u'"')  # left corner bracket
  line = line.replace(u'\u300d', u'"')  # right corner bracket
  line = line.replace(u'\u3003', u'"')  # ditto mark
  line = line.replace(u'\u00a8', u'"')  # diaeresis
  line = line.replace(u'\u0092', u'\'') # curly apostrophe
  line = line.replace(u'\u2019', u'\'') # curly apostrophe
  line = line.replace(u'\uf03d', u'\'') # curly apostrophe
  line = line.replace(u'\u00b4', u'\'') # curly apostrophe
  line = line.replace(u'\u2018', u'\'') # curly single open quote
  line = line.replace(u'\u201a', u'\'') # low-9 quote
  line = line.replace(u'\u0093', u'"')  # curly left quote
  line = line.replace(u'\u201c', u'"')  # curly left quote
  line = line.replace(u'\u0094', u'"')  # curly right quote
  line = line.replace(u'\u201d', u'"')  # curly right quote
  line = line.replace(u'\u2033', u'"')  # curly right quote
  line = line.replace(u'\u201e', u'"')  # low-99 quote
  line = line.replace(u'\u0084', u'"')  # low-99 quote (bad enc)
  line = line.replace(u'\u201f', u'"')  # high-rev-99 quote
  line = line.replace(u'\u00ab', u'"')  # opening guillemet
  line = line.replace(u'\u00bb', u'"')  # closing guillemet
  line = line.replace(u'\u0301', u'\'') # combining acute accent
  line = line.replace(u'\u203a', u'"')  # angle quotation mark
  line = line.replace(u'\u2039', u'"')  # angle quotation mark

  # Space inverted punctuation:
  line = line.replace(u'¡', u' ¡ ')
  line = line.replace(u'¿', u' ¿ ')

  # Russian abbreviations:
  line = line.replace(u' п. п. ', u' п.п. ')
  line = line.replace(u' ст. л. ', u' ст.л. ')
  line = line.replace(u' т. е. ', u' т.е. ')
  line = line.replace(u' т. к. ', u' т.к. ')
  line = line.replace(u' т. ч. ', u' т.ч. ')
  line = line.replace(u' т. д. ', u' т.д. ')
  line = line.replace(u' т. п. ', u' т.п. ')
  line = line.replace(u' и. о. ', u' и.о. ')
  line = line.replace(u' с. г. ', u' с.г. ')
  line = line.replace(u' г. р. ', u' г.р. ')
  line = line.replace(u' т. н. ', u' т.н. ')
  line = line.replace(u' т. ч. ', u' т.ч. ')
  line = line.replace(u' н. э. ', u' н.э. ')

  # Convert foreign numerals into Arabic numerals 
  line = ''.join([str(unicodedata.digit(c)) if c.isdigit() else c for c in line])
   
  # Random punctuation:
  line = line.replace(u'！', u'!')
  line = line.replace(u'-', u'-')
  line = line.replace(u'～', u'~')
  line = line.replace(u'、', u',')
  #line = line.replace(u'。', u'.')
  line = line.replace(u'\u0085', u'...')
  line = line.replace(u'…', u'...')
  line = line.replace(u'―', u'--')
  line = line.replace(u'–', u'--')
  line = line.replace(u'─', u'--')
  line = line.replace(u'—', u'--')
  line = line.replace(u'\u0097', u'--')
  line = line.replace(u'•', u' * ')
  line = line.replace(u'\*', u' * ')
  line = line.replace(u'،', u',')
  line = line.replace(u'؟', u'?')
  line = line.replace(u'ـ', u' ')
  line = line.replace(u'Ã ̄', u'i')
  line = line.replace(u'â€™', u'\'')
  line = line.replace(u'â€"', u'"')
  line = line.replace(u'؛', u';')

  # Regularize ligatures:
  line = line.replace(u'\u009c', u'oe')  # "oe" ligature
  line = line.replace(u'\u0153', u'oe')  # "oe" ligature
  line = line.replace(u'\u008c', u'Oe')  # "OE" ligature
  line = line.replace(u'\u0152', u'Oe')  # "OE" ligature
  line = line.replace(u'\ufb00', u'ff')  # "ff" ligature
  line = line.replace(u'\ufb01', u'fi')  # "fi" ligature
  line = line.replace(u'\ufb02', u'fl')  # "fl" ligature
  line = line.replace(u'\ufb03', u'ffi') # "ffi" ligature
  line = line.replace(u'\ufb04', u'ffl') # "ffl" ligature
  line = line.replace(u'\u0132', u'Ij')  # "Ij" ligature
  line = line.replace(u'\u0133', u'ij')  # "ij" ligature
  line = line.replace(u'\ufb06', u'st')  # "st" ligature
  line = line.replace(u'\u00c6', u'Ae')  # "Ae" ligature
  line = line.replace(u'\u00e6', u'ae')  # "ae" ligature
  line = line.replace(u'\ufb05', u'st')  # "st" ligature

  line = line.replace(u'β', u'ß') # WMT 2010 error

  # Strip extra spaces:
  line = re.sub(ur'\s+', u' ', line)
  line = line.strip()
  return line

### remove punct on the right side
### e.g., xxx@yy.zz, => xxx@yy.zz ,
def proc_rightpunc(token):
  token = re.sub(u'((\u0964' ur'|\.|\,|\;|\!|:|\?|\"|\)|\]|\}|\>|\-)+)$', ur' \1 ', token)
  if re.search(ur'\s', token):
    return tokenize_line(token)
  else:
    return token

#######################################
### return the new token:
###   types of punct:
##      T1 (2):   the punct is always a token by itself no matter where it
###           appears:   " ;
##      T2 (15):  the punct that can be a part of words made of puncts only.
##               ` ! @ + = [ ] < > | ( ) { } ?
##      T3 (15):  the punct can be part of a word that contains [a-z\d]
##        T3: ~ ^ & : , # * % - _ \ / . $ '
##             infix: ~ (12~13), ^ (2^3), & (AT&T),  : ,
##             prefix: # (#9),  * (*3),
##             suffix: % (10%),
##             infix+prefix: - (-5), _ (_foo),
##             more than one position: \ /  . $
##             Appos: 'm n't ...

##   1. separate by puncts in T1
##   2. separate by puncts in T2
##   3. deal with punct T3 one by one according to options
##   4. if the token remains unchanged after step 1-3, return the token
def deep_proc_token(token):
  assert len(token) >= 2
  assert ' ' not in token
  ##### step 0: if it mades up of all puncts, remove one punct at a time.
  # Note: We define "punctuation" as anything not in one of these pre-defined "letter" character classes
  if not re.search(ur'\w|\d', token, flags=re.UNICODE):
    if len(token) > 100:
      return token
    if re.match(ur'^(\!+|\@+|\++|\=+|\*+|\<+|\>+|\|+|\?+|' + u'\u0964' + ur'+|\.+|\-+|\_+|\&+)$', token):
      return token
    match = re.match(ur'^(.)(.+)$', token)
    assert match is not None
    return match.group(1) + ' ' + proc_token(match.group(2))

  ##### step 1.1: separate by quotes on the boundary
  if token[0] == '"':
    s = u'“ ' + token[1:]
    return tokenize_line(s)

  if token[-1] == '"':
    s = token[:-1] + u' ”'
    return tokenize_line(s)

  ##### step 1.2: separate by punct T1 on the boundary
  t1 = ur';'
  s = re.sub(ur'^((' + t1 + ur'))', ur'\1 ', token)
  if s != token:
    return tokenize_line(s)

  s = re.sub(ur'((' + t1 + ur'))$', ur' \1', token)
  if s != token:
    return tokenize_line(s)

  ##### step 1.3: separate by punct T2 in any position
  s = re.sub(ur'((' + t1 + ur'))', ur' \1 ', token)
  if s != token:
    return tokenize_line(s)

  ##### step 2.1: separate by punct T2 on the boundary
  t2 = ur'\`|\!|\@|\+|\=|\[|\]|\<|\>|\||\(|\)|\{|\}|\?|●|○|;'
  s = re.sub(ur'^((' + t2 + ur')+)', ur'\1 ', token)
  if s != token:
    return tokenize_line(s)

  s = re.sub(ur'((' + t2 + ur')+)$', ur' \1', token)
  if s != token:
    return tokenize_line(s)

  ##### step 2.2: separate by punct T2 in any position
  s = re.sub(ur'((' + t2 + ur')+)', ur' \1 ', token)
  if s != token:
    return tokenize_line(s)

  ##### step 3: deal with special puncts in T3.
  # comma on the left
  m = re.match(ur'^(\,+)(.+)$', token)
  if m is not None:
    return proc_token(m.group(1)) + ' ' + proc_token(m.group(2))

  # comma on the right
  m = re.match(ur'^(.*[^\,]+)(\,+)$', token)
  if m is not None:
    ## 19.3,,, => 19.3 ,,,
    return proc_token(m.group(1)) + ' ' + proc_token(m.group(2))

  ## remove the ending periods that follow number etc.
  m = re.match(ur'^(.*(\d|\~|\^|\&|\:|\,|\#|\*|\%|€|\-|\_|\/|\\|\$|\'))(\.+)$', token)
  if m is not None:
    return proc_token(m.group(1)) + ' ' + proc_token(m.group(3))

  ###  deal with "$"
  if args.split_on_dollar_sign > 0:
    if args.split_on_dollar_sign == 1:
      # split on all occasions
      s = re.sub(ur'(\$+)', ur'\1', token)
    else:
      s = re.sub(ur'(\$+)(\d)', ur'\1 \2', token)
    if s != token:
      return tokenize_line(s)

  ### deal with "#"
  if args.split_on_sharp_sign > 0:
    if args.split_on_sharp_sign == 1:
      s = re.sub(ur'(\#+)', ur' \1 ', token)
    else:
      s = re.sub(ur'(\#+)(\D)', ur' \1 \2', token)
    if s != token:
      return tokenize_line(s)

  ## deal with '
  s = re.sub(ur'([^\'])([\']+)$', ur'\1 \2', token)
  s = re.sub(ur'^(\'+)(\w+)', ur' \1 \2', s, flags=re.UNICODE)
  if s != token:
    return tokenize_line(s)

  ## deal with special English abbreviations with '
  ## note that \' and \. could interact: e.g.,  U.S.'s;   're.
  m = re.match(ur'^(.*[a-z]+)(n\'t)([\.]*)$', token, flags=re.IGNORECASE)
  if m is not None:
    return proc_token(m.group(1)) + " " + m.group(2) + " " + proc_token(m.group(3))

  ## 's, 't, 'm,  'll, 're, 've: they've => they 've 
  ## 1950's => 1950 's     Co.'s => Co. 's
  if not args.no_english_apos:
    m = re.match(ur'^(.+)(\'s)(\W*)$', token, flags=re.IGNORECASE)
    if m is not None:
      return proc_token(m.group(1)) + " " + m.group(2) + " " + proc_token(m.group(3))

    m = re.match(ur'^(.*[a-z]+)(\'(m|re|ve|ll|d))(\.*)', token, flags=re.IGNORECASE)
    if m is not None:
      return proc_token(m.group(1)) + " " + m.group(2) + " " + proc_token(m.group(4))

  ## deal with "~"
  if args.split_on_tilde > 0:
    if args.split_on_tilde == 1:
      s = re.sub(ur'(\~+)', ur' \1 ', token)
    else:
      s = re.sub(ur'(\D)(\~+)', ur'\1 \2 ', token)
      s = re.sub(ur'(\~+)(\D)', ur' \1 \2', s)
      s = re.sub(ur'^(\~+)(\d)', ur'\1 \2', s)
      s = re.sub(ur'(\d)(\~+)$', ur'\1 \2', s)
    if s != token:
      return tokenize_line(s)

  ## deal with "^"
  if args.split_on_circ > 0:
    if args.split_on_circ == 1:
      s = re.sub(ur'(\^+)', ur' \1 ', token)
    else:
      s = re.sub(ur'(\D)(\^+)', ur'\1 \2 ', token)
      s = re.sub(ur'(\^+)(\D)', ur' \1 \2', s)
    if s != token:
      return tokenize_line(s)

  ## deal with ":"
  if args.split_on_semicolon > 0:
    s = re.sub(ur'^(\:+)', ur'\1 ', token)
    s = re.sub(ur'(\:+)$', ur' \1', s)
    if args.split_on_semicolon == 1:
      s = re.sub(ur'(\:+)', ur' \1 ', s)
    else:
      s = re.sub(ur'(\D)(\:+)', ur'\1 \2 ', s)
      s = re.sub(ur'(\:+)(\D)', ur' \1 \2', s)
    if s != token:
      return tokenize_line(s)


  ###  deal with hyphen: 1992-1993. 21st-24th
  if args.split_on_dash > 0:
    s = re.sub(ur'(\-{2,})', ur' \1 ', token)
    if args.split_on_dash == 1:
      s = re.sub(ur'([\-]+)', ur' \1 ', s)
    else:
      s = re.sub(ur'(\D)(\-+)', ur'\1 \2 ', s)
      s = re.sub(ur'(\-+)(\D)', ur' \1 \2', s)
    if s != token:
      return tokenize_line(s)

  ## deal with "_"
  if args.split_on_underscore > 0:
    s = re.sub(ur'([\_]+)', ur' \1 ', token)
    if s != token:
      return tokenize_line(s)

  ## deal with "%"
  if args.split_on_percent_sign > 0:
    if args.split_on_percent_sign == 1:
      s = re.sub(ur'(\%+|€+)', ur' \1 ', token)
    else:
      s = re.sub(ur'(\D)(\%+|€+)', ur'\1 \2', token, flags=re.UNICODE)
    if s != token:
      return tokenize_line(s)


  ###  deal with "/": 4/5
  if args.split_on_slash > 0:
    if args.split_on_slash == 1:
      s = re.sub(ur'(\/+)', ur' \1 ', token)
    else:
      s = re.sub(ur'(\D)(\/+)', ur'\1 \2 ', token)
      s = re.sub(ur'(\/+)(\D)', ur' \1 \2', s)
    if s != token:
      return tokenize_line(s)

  ### deal with comma: 123,456
  s = re.sub(ur'([^\d]),', ur'\1 , ', token)      ## xxx, 1923 => xxx , 1923
  s = re.sub(ur',\s*([^\d])', ur' , \1', s)       ## 1923, xxx => 1923 , xxx
  s = re.sub(ur',([\d]{1,2}[^\d])', ur' , \1', s) ## 1,23 => 1 , 23
  s = re.sub(ur',([\d]{4,}[^\d])', ur' , \1', s)  ## 1,2345 => 1 , 2345
  s = re.sub(ur',([\d]{1,2})$', ur' , \1', s)     ## 1,23 => 1 , 23
  s = re.sub(ur',([\d]{4,})$', ur' , \1', s)      ## 1,2345 => 1 , 2345
  if s != token:
    return tokenize_line(s)

  ##  deal with "&"
  if args.split_on_and_sign > 0:
    if args.split_on_and_sign == 1:
      s = re.sub(ur'(\&+)', ur' \1 ', token)
    else:
      s = re.sub(ur'([A-Za-z]{3,})(\&+)', ur'\1 \2 ', token)
      s = re.sub(ur'(\&+)([A-Za-z]{3,})', ur' \1 \2', s)
    if s != token:
      return tokenize_line(s)

  ## deal with period
  if re.match(ur'^(([\+|\-])*(\d+\,)*\d*\.\d+\%*)$', token):
    return token

  m = re.match(ur'^((\w)(\.(\w))+)(\.?)(\.*)$', token, flags=re.UNICODE)
  if m is not None:
    ## I.B.M. 
    t1 = m.group(1) + m.group(5)
    t3 = m.group(6)
    return t1 + " " + proc_token(t3)

  ## Feb.. => Feb. .
  m = re.match(ur'^(.*[^\.])(\.)(\.*)$', token)
  if m is not None:
    p1 = m.group(1)
    p2 = m.group(2)
    p3 = m.group(3)
    p1_lc = p1.lower()
    global dict_hash
    if (p1_lc + p2) in dict_hash:
      return p1 + p2 + ' ' + proc_token(p3)
    elif p1_lc in dict_hash:
      return p1 + ' ' + proc_token(p2 + p3)
    else:
      return proc_token(p1) + ' ' + proc_token(p2 + p3)

  s = re.sub(ur'(\.+)(.+)', ur'\1 \2', token)
  if s != token:
    return tokenize_line(s)

  ##### Final step: separate word-internal quotes in any position
  # These needs to happen AFTER all of the other tokenization, so
  # as to handle cases like value="hello" --> value = “ hello ”
  s = token.replace(u'"', u' " ', 1)
  if s != token:
    return tokenize_line(s)


  ## no pattern applies
  return token

## Tokenize a str that does not contain " ", return the new string
## The function handles the cases that the token needs not be segmented.
## for other cases, it calls deep_proc_token()
def proc_token(token):
  # step 0: it has only one char
  if len(token) <= 1:
    return token

  # step 1: check the most common case
  if re.match(ur'^\w+$', token, flags=re.UNICODE):
    return token

  # step 2: check whether it is some NE entity
  # 1.2.4.6
  if re.match(ur'^\d+(\.\d+)+$', token):
    return token
  if re.match(ur'^\d+(\.\d+)+(亿|百万|万|千)?$', token):
    return token
  ## 1,234,345.34
  if re.match(ur'^\d+(\.\d{3})*,\d+$', token):
    return token
  ## 1.234.345,34
  if re.match(ur'^\d+(,\d{3})*\.\d+$', token):
    return token

  # twitter hashtag or address
  if re.match(ur'^(@|#)(\w|\d|_)+.*$', token, flags=re.UNICODE):
    return proc_rightpunc(token)

  ### email address: xxx@yy.zz
  if re.match(ur'^[a-z0-9\_\-]+\@[a-z\d\_\-]+(\.[a-z\d\_\-]+)*(.*)$', token, flags=re.IGNORECASE):
    return proc_rightpunc(token)

  ### URL: http://xx.yy.zz
  if re.match(ur'^(mailto|http|https|ftp|gopher|telnet|file)\:\/{0,2}([^\.]+)(\.(.+))*$', token, flags=re.IGNORECASE):
    return proc_rightpunc(token)

  ### www.yy.dd/land
  if re.match(ur'^(www)(\.(.+))+$', token, flags=re.IGNORECASE):
    return proc_rightpunc(token)

  ### URL: upenn.edu/~xx
  if re.match(ur'^(\w+\.)+(com|co|edu|org|gov|ly|cz|ru|eu)(\.[a-z]{2,3})?\:{0,2}(\/\S*)?$', token, flags=re.IGNORECASE|re.UNICODE):
    return proc_rightpunc(token)

  ### only handle American phone numbers: e.g., (914)244-4567
  if re.match(ur'^\(\d{3}\)\d{3}(\-\d{4})$', token):
    return proc_rightpunc(token)

  ### /nls/p/....
  if re.match(ur'^\/[-A-Za-z0-9_./]+$', token) and '//' not in token:
    return token

  ### \nls\p\....
  if re.match(ur'^\\((\w|\d|_|\-|\.)+\\)+(\w|\d|_|\-|\.)+\\?$', token):
    return token

  ## step 3: check the dictionary
  global dict_hash
  if token.lower() in dict_hash:
    return token

  ## step 4: call deep tokenization
  return deep_proc_token(token)

def tokenize_line(line):
  line = line.strip()
  line = re.sub(ur'\s+', ' ', line)
  parts = line.split()

  new_parts = []
  for part in parts:
    new_parts.append(proc_token(part))
  return ' '.join(new_parts)

def tokenizer(line):
  line = line.replace(u'\u0970', '.') # Devanagari abbreviation character
  # markup
  if re.search(ur'^(\[b\s+|\]b|\]f|\[f\s+)', line) or \
     re.search(ur'^\[[bf]$', line) or \
     re.search(ur'^\s*$', line) or \
     re.search(ur'^<DOC', line) or \
     re.search(ur'^<\/DOC', line):
    return line
  line = re.sub(u'(\u0964+)', ur' \1', line) #Devanagari end of sentence
  line = tokenize_line(line)
  line = line.strip()
  line = re.sub(ur'\s+', ur' ', line)
  parts = line.split()

  # fix sgm-markup tokenization
  line = re.sub(ur'\s*<\s+seg\s+id\s+=\s+(\d+)\s+>', ur'<seg id=\1>', line)
  line = re.sub(ur'\s*<\s+(p|hl)\s+>', ur'<\1>', line)
  line = re.sub(ur'\s*<\s+(p|hl)\s+>', u'<\1>', line)
  line = re.sub(ur'\s*<\s+\/\s+(p|hl|DOC)\s+>', ur'<\/\1>', line)
  line = re.sub(ur'<\s+\/\s+seg\s+>', u'<\/seg>', line)
  if re.search(ur'^\s*<\s+DOC\s+', line):
    line = re.sub(ur'\s+', u'', line)
    line = line.replace(ur'DOC', u'DOC ')
    line = line.replace(ur'sys', u' sys')
  if re.search(ur'^\s*<\s+(refset|srcset)\s+', line):
    line = re.sub(ur'\s+', u'', line)
    line = re.sub(ur'(set|src|tgt|trg)', ur' \1', line)

  return line

def tokenize(stream):
  for line in utf8_normalize(stream):
    line = quote_norm(line)
    line = tokenizer(line)
    line = re.sub(ur'(\b[Aa])l - ', ur'\1l-', line, flags=re.UNICODE)
    if not args.no_english_apos:
      line = re.sub(ur' \' (s|m|ll|re|d|ve) ', ur" '\1 ", line, flags=re.IGNORECASE)
      line = re.sub(u'n \' t ', u' n\'t ', line, flags=re.IGNORECASE)
    line = line.strip()
    line = re.sub(ur'(\d+)(\.+)$', ur'\1 .', line)
    line = re.sub(ur'(\d+)(\.+)\s*\|\|\|', ur'\1 . |||', line)
    yield line

def load_token_list(filename):
  token_list = set()
  with open(filename) as f:
   for line in f:
     line = line.strip()
     if len(line) > 0:
       token_list.add(line.lower())
  return token_list

parser = argparse.ArgumentParser('Tokenizes text in a reasonable way for most languages. Reads input corpus from stdin and writes results to stdout.')
parser.add_argument('--unbuffered', '-u', action='store_true', help='Use unbuffered line mode')
parser.add_argument('--token_list', type=str, default='/usr1/home/austinma/git/cdec/corpus/support/token_list', help='List of tokens that should not be segmented')
parser.add_argument('--split_on_dollar_sign', type=int, default=2, help='0=Never split, 1=Always split, 2=Split only when followed by a number')
parser.add_argument('--split_on_sharp_sign', type=int, default=2)
parser.add_argument('--split_on_tilde', type=int, default=2)
parser.add_argument('--split_on_circ', type=int, default=2)
parser.add_argument('--split_on_semicolon', type=int, default=2)
parser.add_argument('--split_on_dash', type=int, default=2)
parser.add_argument('--split_on_underscore', type=int, default=0)
parser.add_argument('--split_on_percent_sign', type=int, default=1)
parser.add_argument('--split_on_slash', type=int, default=2)
parser.add_argument('--split_on_and_sign', type=int, default=2)
parser.add_argument('--no_english_apos', action='store_true', help='Don\'t separate the suffices n\'t, \'s, \'m, \'re, \'ve, \'ll and \'d')
args = parser.parse_args()

dict_hash = load_token_list(args.token_list)

output = tokenize(sys.stdin)
for line in output:
  print line.encode('utf-8')
