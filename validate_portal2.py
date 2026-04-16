#!/usr/bin/env python3
import html.parser

parser = html.parser.HTMLParser()
try:
    with open('portal.html', encoding='utf-8') as f:
        content = f.read()
    parser.feed(content)
    print("✅ HTML syntaktisch korrekt (UTF-8)")
except Exception as e:
    print(f"❌ HTML Fehler: {e}")
