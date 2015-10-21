#coding: utf8
import re
import sys
import argparse
import subprocess
import unicodedata

# TODO: I'm worried that \u0000 sequences don't work on utf8 encoded text.

def locate_uconv():
  # Instead of falling back to iconv, throw an error if you can't find uconv
  return '/usr/bin/uconv'

def utf8_normalize(stream):
  uconv_bin = locate_uconv()
  uconv = subprocess.Popen([uconv_bin] + '-f utf8 -t utf8 -x Any-NFKC --callback skip'.split(), stdin=stream, stdout=subprocess.PIPE, shell=False)
  for line in uconv.stdout:
    line = re.sub(r'[\x00-\x1F]+', ' ', line)
    line = re.sub(r'\s+', ' ', line)
    line = line.strip()
    yield line

def html_hex_entity(match):
  u = int(match.group(1), 16)
  return unichr(u).encode('utf-8')

def html_entity(match):
  u = int(match.group(1), 10)
  return unichr(u).encode('utf-8')

# TODO: Break up this megalithic function
def quote_norm(line):
  line = ' %s ' % line
  # Delete control characters:
  line = re.sub(r'[\x00-\x1F]+', ' ', line)

  # PTB --> normal
  line = re.sub(r'-LRB-', '(', line)
  line = re.sub(r'-RRB-', ')', line)
  line = re.sub(r'-LSB-', '[', line)
  line = re.sub(r'-RSB-', ']', line)
  line = re.sub(r'-LCB-', '{', line)
  line = re.sub(r'-RCB-', '}', line)
  line = re.sub(r' gon na ', ' gonna ', line)

  # Regularize named HTML/XML escapes:
  line = re.sub(r'&\s*lt\s*;', '<', line, flags=re.IGNORECASE)     # HTML opening angle bracket
  line = re.sub(r'&\s*gt\s*;', '>', line, flags=re.IGNORECASE)     # HTML closing angle bracket
  line = re.sub(r'&\s*squot\s*;', '\'', line, flags=re.IGNORECASE) # HTML single quote
  line = re.sub(r'&\s*quot\s*;', '"', line, flags=re.IGNORECASE)   # HTML double quote
  line = re.sub(r'&\s*nbsp\s*;', ' ', line, flags=re.IGNORECASE)   # HTML non-breaking space
  line = re.sub(r'&\s*apos\s*;', '\'', line, flags=re.IGNORECASE)  # HTML apostrophe
  line = re.sub(r'&\s*amp\s*;', '&', line, flags=re.IGNORECASE)    # HTML ampersand (last)

  # Regularize known HTML numeric codes:
  line = re.sub(r'&\s*#\s*160\s*;', ' ', line)
  line = re.sub(r'&\s*#45\s*;\s*&\s*#45\s*;', '--', line)
  line = re.sub(r'&\s*#45\s*;', '--', line)

  # Convert arbitrary hex or decimal HTML entities to actual characters:
  line = re.sub(r'&\#x([0-9A-Fa-f]+);', html_hex_entity, line)
  line = re.sub(r'&\#([0-9]+);', html_entity, line)

  # Regularlize spaces:
  line = re.sub('\u00ad', '', line)  # soft hyphen
  line = re.sub('\u200C', '', line)  # zero-width non-joiner
  line = re.sub('\u00a0', ' ', line) # non-breaking space
  line = re.sub('\u2009', ' ', line) # thin space
  line = re.sub('\u2028', ' ', line) # "line separator"
  line = re.sub('\u2029', ' ', line) # "paragraph separator"
  line = re.sub('\u202a', ' ', line) # "left-to-right embedding"
  line = re.sub('\u202b', ' ', line) # "right-to-left embedding"
  line = re.sub('\u202c', ' ', line) # "pop directional formatting"
  line = re.sub('\u202d', ' ', line) # "left-to-right override"
  line = re.sub('\u202e', ' ', line) # "right-to-left override"
  line = re.sub('\u0085', ' ', line) # "next line"
  line = re.sub('\ufffd', ' ', line) # "replacement character"
  line = re.sub('\ufeff', ' ', line) # byte-order mark
  line = re.sub('\ufdd3', ' ', line) # "unicode non-character"

  # Convert other Windows 1252 characters to UTF-8
  line = re.sub('\u0080', '\u20ac', line) # euro sign
  line = re.sub('\u0095', '\u2022', line) # bullet
  line = re.sub('\u0099', '\u2122', line) # trademark sign

  # Currency and measure conversions:
  line = re.sub(r' (\d\d): (\d\d)', r' \1:\2', line)
  line = re.sub('\u20a0', ' EUR ', line)
  line = re.sub('\u20ac', ' EUR ', line)
  line = re.sub('\u00a3', ' GBP ', line)
  line = re.sub(r'(\W)([A-Z]+\$?)(\d*\.\d+|\d+)', r'\1\2 \3', line)
  line = re.sub(r'(\W)(euro?)(\d*\.\d+|\d+)', r'\1EUR \3', line)

  # Ridiculous double conversions, UTF8 -> Windows 1252 -> UTF8:
  line = re.sub('ï¿½c', '--', line)                 # long dash
  line = re.sub('\u00e2\u20acoe', '"', line)        # opening double quote
  line = re.sub('\u00e2\u20ac\u009c', '"', line)    # opening double quote
  line = re.sub('\u00e2\u20ac\u009d', '"', line)    # closing double quote
  line = re.sub('\u00e2\u20ac\u2122', '\'', line)   # apostrophe
  line = re.sub('\u00e2\u20ac\u201c', ' -- ', line) # en dash?
  line = re.sub('\u00e2\u20ac\u201d', ' -- ', line) # em dash?

  line = re.sub('\u00e2\u0080(\u0099|\u0098)', r'\'', line) # single quote?
  line = re.sub('\u00e2\u0080(\u009c|\u009d)', r'"', line) # double quote?
  line = re.sub('\u00c3\u009f', '\u00df', line) # esset
  line = re.sub('\u00c3\u0178', '\u00df', line) # esset
  line = re.sub('\u00c3\u00a4', '\u00e4', line) # a umlaut
  line = re.sub('\u00c3\u00b6', '\u00f6', line) # o umlaut
  line = re.sub('\u00c3\u00bc', '\u00fc', line) # u umlaut
  line = re.sub('\u00c3\u0084', '\u00c4', line) # A umlaut: create no C4s after this
  line = re.sub('\u00c3\u201e', '\u00c4', line) # A umlaut: create no C4s after this
  line = re.sub('\u00c3\u0096', '\u00d6', line) # O umlaut
  line = re.sub('\u00c3\u2013', '\u00d6', line) # O umlaut
  line = re.sub('\u00c3\u00bc', '\u00dc', line) # U umlaut
  line = re.sub('\u0080', '\20ac', line)        # euro sign
  line = re.sub('\u0095', '\2022', line)        # bullet
  line = re.sub('\u0099', '\2122', line)        # trademark sign

  # Regularize quotes:
  line = re.sub('ˇ', '\'', line)      # caron
  line = re.sub('´', '\'', line)      # acute accent
  line = re.sub('`', '\'', line)      # grave accent
  line = re.sub('ˉ', '\'', line)      # modified letter macron
  line = re.sub(' ,,', '"', line)     # ghetto low-99 quote
  line = re.sub('``', '"', line)      # latex-style left quote
  line = re.sub('\'\'', '"', line)    # latex-style right quote
  line = re.sub('\u300c', '"', line)  # left corner bracket
  line = re.sub('\u300d', '"', line)  # right corner bracket
  line = re.sub('\u3003', '"', line)  # ditto mark
  line = re.sub('\u00a8', '"', line)  # diaeresis
  line = re.sub('\u0092', '\'', line) # curly apostrophe
  line = re.sub('\u2019', '\'', line) # curly apostrophe
  line = re.sub('\uf03d', '\'', line) # curly apostrophe
  line = re.sub('\u00b4', '\'', line) # curly apostrophe
  line = re.sub('\u2018', '\'', line) # curly single open quote
  line = re.sub('\u201a', '\'', line) # low-9 quote
  line = re.sub('\u0093', '"', line)  # curly left quote
  line = re.sub('\u201c', '"', line)  # curly left quote
  line = re.sub('\u0094', '"', line)  # curly right quote
  line = re.sub('\u201d', '"', line)  # curly right quote
  line = re.sub('\u2033', '"', line)  # curly right quote
  line = re.sub('\u201e', '"', line)  # low-99 quote
  line = re.sub('\u0084', '"', line)  # low-99 quote (bad enc)
  line = re.sub('\u201f', '"', line)  # high-rev-99 quote
  line = re.sub('\u00ab', '"', line)  # opening guillemet
  line = re.sub('\u00bb', '"', line)  # closing guillemet
  line = re.sub('\u0301', '\'', line) # combining acute accent
  line = re.sub('\u203a', '"', line)  # angle quotation mark
  line = re.sub('\u2039', '"', line)  # angle quotation mark

  # Space inverted punctuation:
  line = re.sub('¡', ' ¡ ', line)
  line = re.sub('¿', ' ¿ ', line)

  # Russian abbreviations:
  line = re.sub(' п. п. ', ' п.п. ', line)
  line = re.sub(' ст. л. ', ' ст.л. ', line)
  line = re.sub(' т. е. ', ' т.е. ', line)
  line = re.sub(' т. к. ', ' т.к. ', line)
  line = re.sub(' т. ч. ', ' т.ч. ', line)
  line = re.sub(' т. д. ', ' т.д. ', line)
  line = re.sub(' т. п. ', ' т.п. ', line)
  line = re.sub(' и. о. ', ' и.о. ', line)
  line = re.sub(' с. г. ', ' с.г. ', line)
  line = re.sub(' г. р. ', ' г.р. ', line)
  line = re.sub(' т. н. ', ' т.н. ', line)
  line = re.sub(' т. ч. ', ' т.ч. ', line)
  line = re.sub(' н. э. ', ' н.э. ', line)

  # Convert foreign numerals into Arabic numerals
  line = line.decode('utf-8')
  line = ''.join([str(unicodedata.digit(c)) if c.isdigit() else c for c in line])
  line = line.encode('utf-8')
   
  # Hopefully the above handles all of these cases
  #tr/०-९/0-9/; # devangari, starts at \u0966
  #tr/౦-౯/0-9/; # telugu, starts at \u0c66
  #tr/೦-೯/0-9/; # kannada, starts at \u0ce6
  #tr/೦-௯/0-9/; # tamil, starts at \u0be6
  #tr/൦-൯/0-9/; # malayalam, starts at \u0d66
  # Other interesting digit sets:
  # bengali (09e6), gurmukhi (0a66), jugarati (0ae6), oriya (0b66)
  # sinhala lith (0de6), thai (0e50), lao (0ed0), tiben (0f20)
  # myanmar (1040/1090), kmer (17e0), mongolian (1810), limbu (1946)
  # new tai (19d0), tai tham (1a80/1a90), balinese (1b50), sudanese (1bb0)
  # lepcha (1c40), ol chiki (1c50), vai (a620), saurashtra (a8d0)
  # kayah li (a900), javanese (a9d0), myanmar tai laing (a9f0), cham(aa50)
  # meetei (abf0), osmanya (104a0), rhami (11066), sora sompeng (110f0)
  # chkma (11136), sharada (111d0), khudawadi (112f0), tirhuta (114d0),
  # modi (11650), takri (116c0), ahom (11730), warang citi (118e0)
  # mro (16a60), pahawn hmong (16b50)

  # Random punctuation:
  line = re.sub('！', '!', line)
  line = re.sub('-', '-', line)
  line = re.sub('～', '~', line)
  line = re.sub('、', ',', line)
  #line = re.sub('。', '.', line) # This line was commented out in the perl version too
  line = re.sub('\u0085', '...', line)
  line = re.sub('…', '...', line)
  line = re.sub('―', '--', line)
  line = re.sub('–', '--', line)
  line = re.sub('─', '--', line)
  line = re.sub('—', '--', line)
  line = re.sub('\u0097', '--', line)
  line = re.sub('•', ' * ', line)
  line = re.sub('\*', ' * ', line)
  line = re.sub('،', ',', line)
  line = re.sub('؟', '?', line)
  line = re.sub('ـ', ' ', line)
  line = re.sub('Ã ̄', 'i', line)
  line = re.sub('â€™', '\'', line)
  line = re.sub('â€"', '"', line)
  line = re.sub('؛', ';', line)

  # Regularize ligatures:
  line = re.sub('\u009c', 'oe', line)  # "oe" ligature
  line = re.sub('\u0153', 'oe', line)  # "oe" ligature
  line = re.sub('\u008c', 'Oe', line)  # "OE" ligature
  line = re.sub('\u0152', 'Oe', line)  # "OE" ligature
  line = re.sub('\ufb00', 'ff', line)  # "ff" ligature
  line = re.sub('\ufb01', 'fi', line)  # "fi" ligature
  line = re.sub('\ufb02', 'fl', line)  # "fl" ligature
  line = re.sub('\ufb03', 'ffi', line) # "ffi" ligature
  line = re.sub('\ufb04', 'ffl', line) # "ffl" ligature

  line = re.sub('β', 'ß', line) # WMT 2010 error

  # Strip extra spaces:
  line = re.sub(r'\s+', ' ', line)
  line = line.strip()
  return line

### remove punct on the right side
### e.g., xxx@yy.zz, => xxx@yy.zz ,
def proc_rightpunc(token):
  token = re.sub('((\u0964' r'|\.|\,|\;|\!|:|\?|\"|\)|\]|\}|\>|\-)+)$', r' \1 ', token)
  if re.search(r'\s', token):
    return tokenize_line(token)
  else:
    return token

#######################################
### return the new token:
###   types of punct:
##      T1 (2):   the punct is always a token by itself no matter where it
###           appears:   " ;
##      T2 (15):  the punct that can be a part of words made of puncts only.
##               ` ! @ = [ ] ( ) { } | < > ?
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
  if not re.search(r'\w|\d', token, flags=re.UNICODE):
    if re.match(r'^(\!+|\@+|\++|\=+|\*+|\<+|\>+|\|+|\?+|' '\u0964' + r'+|\.+|\-+|\_+|\&+)$', token):
      return token
    match = re.match(r'^(.)(.+)$', token)
    assert match is not None
    return match.group(1) + ' ' + proc_token(match.group(2))

  ##### step 1: separate by punct T2 on the boundary
  t2 = r'\`|\!|\@|\+|\=|\[|\]|\<|\>|\||\(|\)|\{|\}|\?|\"|;|●|○'
  s = re.sub(r'^((' + t2 + r')+)', r'\1 ', token)
  if s != token:
    s = re.sub('"', '“', s, 1)
    return tokenize_line(s)

  s = re.sub(r'((' + t2 + r')+)$', r' \1', token)
  if s != token:
    s = re.sub('"', '”', s)
    return tokenize_line(s)

  ##### step 2: separate by punct T2 in any position
  s = re.sub(r'((' + t2 + r')+)', r' \1 ', token)
  if s != token:
    s = re.sub('"', '”', s) # probably before punctuation char
    return tokenize_line(s)

  ##### step 3: deal with special puncts in T3.
  # comma on the left
  m = re.match(r'^(\,+)(.+)$', token)
  if m is not None:
    return proc_token(m.group(1)) + ' ' + proc_token(m.group(2))

  # comma on the right
  m = re.match(r'^(.*[^\,]+)(\,+)$', token)
  if m is not None:
    ## 19.3,,, => 19.3 ,,,
    return proc_token(m.group(1)) + ' ' + proc_token(m.group(2))

  ## remove the ending periods that follow number etc.
  m = re.match(r'^(.*(\d|\~|\^|\&|\:|\,|\#|\*|\%|€|\-|\_|\/|\\|\$|\'))(\.+)$', token)
  if m is not None:
    return proc_token(m.group(1)) + ' ' + proc_token(m.group(3))

  ###  deal with "$"
  if args.split_on_dollar_sign > 0:
    if args.split_on_dollar_sign == 1:
      # split on all occasions
      s = re.sub(r'(\$+)', r'\1', token)
    else:
      s = re.sub(r'(\$+)(\d)', r'\1 \2', token)
    if s != token:
      return tokenize_line(s)

  ### deal with "#"
  if args.split_on_sharp_sign > 0:
    if args.split_on_sharp_sign == 1:
      s = re.sub(r'(\#+)', r' \1 ', token)
    else:
      s = re.sub(r'(\#+)(\D)', r' \1 \2', token)
    if s != token:
      return tokenize_line(s)

  ## deal with '
  s = re.sub(r'([^\'])([\']+)$', r'\1 \2', token)
  s = re.sub(r'^(\'+)(\w+)', r' \1 \2', s, flags=re.UNICODE)
  if s != token:
    return tokenize_line(s)

  ## deal with special English abbreviations with '
  ## note that \' and \. could interact: e.g.,  U.S.'s;   're.
  m = re.match(r'^(.*[a-z]+)(n\'t)([\.]*)$', token, flags=re.IGNORECASE)
  if m is not None:
    return proc_token(m.group(1)) + " " + m.group(2) + " " + proc_token(m.group(3))

  ## 's, 't, 'm,  'll, 're, 've: they've => they 've 
  ## 1950's => 1950 's     Co.'s => Co. 's
  if not args.no_english_apos:
    m = re.match(r'^(.+)(\'s)(\W*)$', token, flags=re.IGNORECASE)
    if m is not None:
      return proc_token(m.group(1)) + " " + m.group(2) + " " + proc_token(m.group(3))

    m = re.match(r'^(.*[a-z]+)(\'(m|re|ve|ll|d))(\.*)', token, flags=re.IGNORECASE)
    if m is not None:
      return proc_token(m.group(1)) + " " + m.group(2) + " " + proc_token(m.group(4))

  ## deal with "~"
  if args.split_on_tilde > 0:
    if args.split_on_tilde == 1:
      s = re.sub(r'(\~+)', r' \1 ', token)
    else:
      s = re.sub(r'(\D)(\~+)', r'\1 \2 ', token)
      s = re.sub(r'(\~+)(\D)', r' \1 \2', s)
      s = re.sub(r'^(\~+)(\d)', r'\1 \2', s)
      s = re.sub(r'(\d)(\~+)$', r'\1 \2', s)
    if s != token:
      return tokenize_line(s)

  ## deal with "^"
  if args.split_on_circ > 0:
    if args.split_on_circ == 1:
      s = re.sub(r'(\^+)', r' \1 ', token)
    else:
      s = re.sub(r'(\D)(\^+)', r'\1 \2 ', token)
      s = re.sub(r'(\^+)(\D)', r' \1 \2', s)
    if s != token:
      return tokenize_line(s)

  ## deal with ":"
  if args.split_on_semicolon > 0:
    s = re.sub(r'^(\:+)', r'\1 ', token)
    s = re.sub(r'(\:+)$', r' \1', s)
    if args.split_on_semicolon == 1:
      s = re.sub(r'(\:+)', r' \1 ', s)
    else:
      s = re.sub(r'(\D)(\:+)', r'\1 \2 ', s)
      s = re.sub(r'(\:+)(\D)', r' \1 \2', s)
    if s != token:
      return tokenize_line(s)


  ###  deal with hyphen: 1992-1993. 21st-24th
  if args.split_on_dash > 0:
    s = re.sub(r'(\-{2,})', r' \1 ', token)
    if args.split_on_dash == 1:
      s = re.sub(r'([\-]+)', r' \1 ', s)
    else:
      s = re.sub(r'(\D)(\-+)', r'\1 \2 ', s)
      s = re.sub(r'(\-+)(\D)', r' \1 \2', s)
    if s != token:
      return tokenize_line(s)

  ## deal with "_"
  if args.split_on_underscore > 0:
    s = re.sub(r'([\_]+)', r' \1 ', token)
    if s != token:
      return tokenize_line(s)

  ## deal with "%"
  if args.split_on_percent_sign > 0:
    if args.split_on_percent_sign == 1:
      s = re.sub(r'(\%+|€+)', r' \1 ', token)
    else:
      s = re.sub(r'(\D)(\%+|€+)', r'\1 \2', token)
  if s != token:
    return tokenize_line(s)


  ###  deal with "/": 4/5
  if args.split_on_slash > 0:
    if args.split_on_slash == 1:
      s = re.sub(r'(\/+)', r' \1 ', token)
    else:
      s = re.sub(r'(\D)(\/+)', r'\1 \2 ', token)
      s = re.sub(r'(\/+)(\D)', r' \1 \2', s)
    if s != token:
      return tokenize_line(s)

  ### deal with comma: 123,456
  s = re.sub(r'([^\d]),', r'\1 , ', token)      ## xxx, 1923 => xxx , 1923
  s = re.sub(r',\s*([^\d])', r' , \1', s)       ## 1923, xxx => 1923 , xxx
  s = re.sub(r',([\d]{1,2}[^\d])', r' , \1', s) ## 1,23 => 1 , 23
  s = re.sub(r',([\d]{4,}[^\d])', r' , \1', s)  ## 1,2345 => 1 , 2345
  s = re.sub(r',([\d]{1,2})$', r' , \1', s)     ## 1,23 => 1 , 23
  s = re.sub(r',([\d]{4,})$', r' , \1', s)      ## 1,2345 => 1 , 2345
  if s != token:
    return tokenize_line(s)

  ##  deal with "&"
  if args.split_on_and_sign > 0:
    if args.split_on_and_sign == 1:
      s = re.sub(r'(\&+)', r' \1 ', token)
    else:
      s = re.sub(r'([A-Za-z]{3,})(\&+)', r'\1 \2 ', token)
      s = re.sub(r'(\&+)([A-Za-z]{3,})', r' \1 \2', s)
    if s != token:
      return tokenize_line(s)

  ## deal with period
  if re.match(r'^(([\+|\-])*(\d+\,)*\d*\.\d+\%*)$', token):
    return token

  m = re.match(r'^((\w)(\.(\w))+)(\.?)(\.*)$', token, flags=re.UNICODE)
  if m is not None:
    ## I.B.M. 
    t1 = m.group(1) + m.group(5)
    t3 = m.group(6)
    return t1 + " " + proc_token(t3)

  ## Feb.. => Feb. .
  m = re.match(r'^(.*[^\.])(\.)(\.*)$', token)
  if m is not None:
    p1 = m.group(1)
    p2 = m.group(2)
    p3 = m.group(3)
    p1_lc = p1.lower()
    global dict_hash
    if (p1_lc + p2) in dict_hash:
      return p1 + p2 + " " + proc_token(p3)
    elif p1_lc in dict_hash:
      return p1 + " " + proc_token(p2 + p3)
    else:
      return proc_token(p1) + ' ' + proc_token(p2 + p3)

  s = re.sub(r'(\.+)(.+)', r'\1 \2', token)
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
  if re.match(r'^\w+$', token, flags=re.UNICODE):
    return token

  # step 2: check whether it is some NE entity
  # 1.2.4.6
  if re.match(r'^\d+(.\d+)+$', token):
    return token
  if re.match(r'^\d+(.\d+)+(亿|百万|万|千)?$', token):
    return token
  ## 1,234,345.34
  if re.match(r'^\d+(\.\d{3})*,\d+$', token):
    return token
  ## 1.234.345,34
  if re.match(r'^\d+(,\d{3})*\.\d+$', token):
    return token

  # twitter hashtag or address
  if re.match(r'^(@|#)(\w|\d|_)+.*$', token, flags=re.UNICODE):
    return proc_rightpunc(token)

  ### email address: xxx@yy.zz
  if re.match(r'^[a-z0-9\_\-]+\@[a-z\d\_\-]+(\.[a-z\d\_\-]+)*(.*)$', token, flags=re.IGNORECASE):
    return proc_rightpunc(token)

  ### URL: http://xx.yy.zz
  if re.match(r'^(mailto|http|https|ftp|gopher|telnet|file)\:\/{0,2}([^\.]+)(\.(.+))*$', token, flags=re.IGNORECASE):
    return proc_rightpunc(token)

  ### www.yy.dd/land
  if re.match(r'^(www)(\.(.+))+$', token, flags=re.IGNORECASE):
    return proc_rightpunc(token)

  ### URL: upenn.edu/~xx
  if re.match(r'^(\w+\.)+(com|co|edu|org|gov|ly|cz|ru|eu)(\.[a-z]{2,3})?\:{0,2}(\/\S*)?$', token, flags=re.IGNORECASE|re.UNICODE):
    return proc_rightpunc(token)

  ### only handle American phone numbers: e.g., (914)244-4567
  if re.match(r'^\(\d{3}\)\d{3}(\-\d{4})$', token):
    return proc_rightpunc(token)

  ### /nls/p/....
  if re.match(r'^\/((\w|\d|_|\-|\.)+\/)+(\w|\d|_|\-|\.)+\/?$', token):
    return token

  ### \nls\p\....
  if re.match(r'^\\((\w|\d|_|\-|\.)+\\)+(\w|\d|_|\-|\.)+\\?$', token):
    return token

  ## step 3: check the dictionary
  global dict_hash
  if token.lower() in dict_hash:
    return token

  ## step 4: check word_patterns
  # TODO: where do these patterns come from?
  #for pattern in word_patterns:
  #  if re.search(pattern, token.lower()):
  #    return token

  ## step 5: call deep tokenization
  return deep_proc_token(token)

def tokenize_line(line):
  line = line.strip()
  line = re.sub(r'\s+', ' ', line)
  parts = line.split()

  new_parts = []
  for part in parts:
    new_parts.append(proc_token(part))
  return ' '.join(new_parts)

def tokenizer(line):
  line = re.sub('\u0970', '.', line) # Devanagari abbreviation character
  # markup
  if re.search(r'^(\[b\s+|\]b|\]f|\[f\s+)', line) or \
     re.search(r'^\[[bf]$', line) or \
     re.search(r'^\s*$', line) or \
     re.search(r'^<DOC', line) or \
     re.search(r'^<\/DOC', line):
    return line
  line = re.sub('(\u0964+)',r' \1', line) #Devanagari end of sentence
  line = tokenize_line(line)
  line = line.strip()
  line = re.sub(r'\s+', ' ', line)
  parts = line.split()

  # fix sgm-markup tokenization
  line = re.sub(r'\s*<\s+seg\s+id\s+=\s+(\d+)\s+>', r'<seg id=\1>', line)
  line = re.sub(r'\s*<\s+(p|hl)\s+>', r'<\1>', line)
  line = re.sub(r'\s*<\s+(p|hl)\s+>', '<\1>', line)
  line = re.sub(r'\s*<\s+\/\s+(p|hl|DOC)\s+>', r'<\/\1>', line)
  line = re.sub(r'<\s+\/\s+seg\s+>', '<\/seg>', line)
  if re.search(r'^\s*<\s+DOC\s+', line):
    line = re.sub(r'\s+', '', line)
    line = re.sub(r'DOC', 'DOC ', line)
    line = re.sub(r'sys', ' sys', line)
  if re.search(r'^\s*<\s+(refset|srcset)\s+', line):
    line = re.sub(r'\s+', '', line)
    line = re.sub(r'(set|src|tgt|trg)', r' \1', line)

  return line

def tokenize(stream):
  for line in utf8_normalize(stream):
    line = quote_norm(line)
    line = tokenizer(line)
    #s/(\p{Devanagari}{2}[A-Za-z0-9! ,.\@\p{Devanagari}]+?)\s+(\.)(\s*$|\s+\|\|\|)/$1 \x{0964}$3/s;
    line = re.sub(' al - ', ' al-', line)
    if not args.no_english_apos:
      line = re.sub(r' \' (s|m|ll|re|d|ve) ', r" '\1 ", line, flags=re.IGNORECASE)
      line = re.sub('n \' t ', ' n\'t ', line, flags=re.IGNORECASE)
    line = line.strip()
    #s/(\d+)(\.+)$/$1 ./
    #s/(\d+)(\.+) \|\|\|/$1 . |||/;
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
parser.add_argument('--split_on_dollar_sign', type=int, default=2)
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
  print line
