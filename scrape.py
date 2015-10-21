import os
import re
import sys
import subprocess

# We want to get a couple of sentences in each language available on wikipedia. We do this as follows:
# 1. Look at the language's "abstract" file, which gives the titles and link to articles in the language:
#   wget -O - http://dumps.wikimedia.org/jawiki/latest/jawiki-latest-abstract.xml | grep -o '<link>.*<\/link>' | sed 's/^<link>//' | sed 's/<\/link>//' | rev | cut -f 2- -d# | rev | uniq | head
# 2. Grab an article and search for paragraph tags therewithin:
#   wget -O - https://ja.wikipedia.org/wiki/%E3%82%A2%E3%83%B3%E3%83%91%E3%82%B5%E3%83%B3%E3%83%89 2>/dev/null | sed 's/\n/ /' | grep -o -P '<p>.+?<\/p>' | head | sed 's/<[^>]*>//g'
# We can do this in a loop until we have a sufficient amount of text in a langauge

link_regex = re.compile(r'<link>(.*)#([^#]*)</link>')
paragraph_regex = re.compile(r'<p>.+?</p>')
tag_regex = re.compile(r'<[^ ][^>*]*>')
devnull = open(os.devnull, 'w')

def sample_language(lang_code):
  abstract_url = 'http://dumps.wikimedia.org/%swiki/latest/%swiki-latest-abstract.xml' % (lang_code, lang_code)
  p1 = subprocess.Popen(['wget', '-O', '-', abstract_url], stdout=subprocess.PIPE, stderr=devnull)
 
  sample_paragraphs = set()
  visited_links = set()
  for line in iter(p1.stdout.readline, ''):
    m = link_regex.search(line)
    if m != None:
      page_link = m.group(1)
      if page_link in visited_links:
        continue
      visited_links.add(page_link)
      for i, paragraph in enumerate(harvest_paragraphs(page_link)):
        sample_paragraphs.add(paragraph)
        if i > 3:
          break
      if len(sample_paragraphs) > 20:
        break
  p1.kill()
  return sample_paragraphs

def harvest_paragraphs(page_link):
  p2 = subprocess.Popen(['wget', '-O' '-', page_link], stdout=subprocess.PIPE, stderr=devnull)
  output = p2.stdout.read()
  paragraphs = paragraph_regex.findall(output)
  p2.kill()
  for paragraph in paragraphs:
    paragraph = tag_regex.sub('', paragraph)
    yield paragraph
lang_codes = ['en', 'sv', 'de', 'nl', 'fr', 'ru', 'war', 'ceb', 'it', 'es', 'vi', 'pl', 'ja', 'pt', 'zh', 'uk', 'ca', 'fa', 'sh', 'no', 'ar', 'fi', 'id', 'hu', 'ro', 'cs', 'ko', 'sr', 'ms', 'tr', 'min', 'eo', 'kk', 'da', 'eu', 'bg', 'sk', 'hy', 'he', 'lt', 'hr', 'sl', 'et', 'uz', 'gl', 'nn', 'la', 'vo', 'simple', 'el', 'be', 'ce', 'hi', 'ka', 'az', 'th', 'oc', 'mk', 'ur', 'mg', 'new', 'ta', 'cy', 'tt', 'pms', 'bs', 'tl', 'lv', 'te', 'zh-min-nan', 'be-x-old', 'br', 'ht', 'sq', 'jv', 'ky', 'lb', 'mr', 'zh-yue', 'ml', 'is', 'tg', 'bn', 'af', 'ga', 'ba', 'sco', 'pnb', 'cv', 'fy', 'lmo', 'my', 'yo', 'an', 'sw', 'ne', 'ast', 'io', 'gu', 'scn', 'bpy', 'nds', 'ku', 'als', 'qu', 'pa', 'su', 'kn', 'ckb', 'bar', 'mn', 'ia', 'arz', 'nap', 'bug', 'bat-smg', 'wa', 'gd', 'am', 'map-bms', 'yi', 'mzn', 'fo', 'si', 'nah', 'vec', 'sah', 'li', 'os', 'mrj', 'sa', 'or', 'hsb', 'roa-tara', 'pam', 'mhr', 'se', 'ilo', 'mi', 'azb', 'bcl', 'hif', 'gan', 'ps', 'hak', 'diq', 'bh', 'glk', 'rue', 'nds-nl', 'vls', 'bo', 'fiu-vro', 'xmf', 'co', 'tk', 'sc', 'vep', 'sd', 'lrc', 'gv', 'km', 'csb', 'kv', 'eml', 'crh', 'zea', 'frr', 'zh-classical', 'wuu', 'as', 'so', 'szl', 'udm', 'ay', 'kw', 'stq', 'nrm', 'rm', 'koi', 'lad', 'cdo', 'ie', 'fur', 'mt', 'pcd', 'gn', 'dv', 'dsb', 'lij', 'cbk-zam', 'ksh', 'gag', 'myv', 'ext', 'mwl', 'ang', 'lez', 'nso', 'ace', 'ug', 'pi', 'pag', 'kab', 'nv', 'frp', 'sn', 'ln', 'av', 'haw', 'pfl', 'xal', 'krc', 'kaa', 'rw', 'pdc', 'to', 'kl', 'arc', 'nov', 'kbd', 'gom', 'bxr', 'lo', 'bjn', 'ha', 'mai', 'tet', 'pap', 'tpi', 'na', 'tyv', 'lbe', 'jbo', 'roa-rup', 'ty', 'mdf', 'za', 'ig', 'wo', 'srn', 'kg', 'ab', 'ltg', 'zu', 'om', 'lg', 'rmy', 'chy', 'cu', 'tw', 'tn', 'chr', 'bi', 'pih', 'got', 'sm', 'ss', 'xh', 'rn', 'ki', 'pnt', 'bm', 'iu', 'ee', 'st', 'ts', 'ks', 'fj', 'ak', 'sg', 'ik', 've', 'ff', 'ny', 'ti', 'ch', 'dz', 'tum', 'cr']
for lang_code in lang_codes:
  lang_code = re.sub('-', '_', lang_code)
  paragraphs = sample_language(lang_code)
  if len(paragraphs) > 0:
    sample_file = open(os.path.join('samples', '%s.txt' % lang_code), 'w')
    for paragraph in paragraphs:
      sample_file.write(paragraph)
      sample_file.write('\n')
    sample_file.close()
    print 'Successfully sampled language %s' % lang_code
  else:
    print 'Unable to get sample of language %s' % lang_code
