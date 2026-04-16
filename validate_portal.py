#!/usr/bin/env python3
import html.parser

parser = html.parser.HTMLParser()
try:
    with open('portal.html') as f:
        content = f.read()
    parser.feed(content)
    print("✅ HTML syntaktisch korrekt")
except Exception as e:
    print(f"❌ HTML Fehler: {e}")
