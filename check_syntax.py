import re

with open('lernapp.html', encoding='utf-8') as f:
    content = f.read()

s = content.find('<script>') + 8
e = content.rfind('</script>')
js = content[s:e]

# Proper JS brace counter that skips strings, template literals and comments
depth = 0
i = 0
errors = []
line_num = 1

while i < len(js):
    c = js[i]
    
    if c == '\n':
        line_num += 1
        i += 1
        continue
    
    # Skip single-line comments
    if c == '/' and i+1 < len(js) and js[i+1] == '/':
        while i < len(js) and js[i] != '\n':
            i += 1
        continue
    
    # Skip multi-line comments
    if c == '/' and i+1 < len(js) and js[i+1] == '*':
        i += 2
        while i+1 < len(js) and not (js[i] == '*' and js[i+1] == '/'):
            if js[i] == '\n':
                line_num += 1
            i += 1
        i += 2
        continue
    
    # Skip template literals (backtick strings)
    if c == '`':
        i += 1
        tdepth = 0
        while i < len(js):
            if js[i] == '\\':
                i += 2
                continue
            if js[i] == '\n':
                line_num += 1
            if js[i] == '`' and tdepth == 0:
                i += 1
                break
            if js[i] == '$' and i+1 < len(js) and js[i+1] == '{':
                tdepth += 1
                i += 2
                continue
            if js[i] == '}' and tdepth > 0:
                tdepth -= 1
                i += 1
                continue
            i += 1
        continue
    
    # Skip double-quoted strings
    if c == '"':
        i += 1
        while i < len(js) and js[i] != '"':
            if js[i] == '\\':
                i += 1
            i += 1
        if i < len(js):
            i += 1
        continue
    
    # Skip single-quoted strings
    if c == "'":
        i += 1
        while i < len(js) and js[i] != "'":
            if js[i] == '\\':
                i += 1
            i += 1
        if i < len(js):
            i += 1
        continue
    
    if c == '{':
        depth += 1
    elif c == '}':
        depth -= 1
        if depth < 0:
            errors.append(f'Negative depth at JS line {line_num}')
    
    i += 1

print(f'Final depth: {depth}')
if errors:
    for e in errors:
        print(e)
else:
    print('No negative depth errors found')

if depth == 0:
    print('BRACES BALANCED OK')
else:
    print(f'MISMATCH: {depth} unclosed braces')
