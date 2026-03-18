import re

with open('old_index_reference.html', 'r', encoding='utf-8') as f:
    old_html = f.read()

with open('templates/index.html', 'r', encoding='utf-8') as f:
    new_html = f.read()

script_start = old_html.find('<script>')
script_end = old_html.rfind('</script>')
old_js = old_html[script_start+8:script_end]

# we have new_html. we will inject a robust version of JS.
