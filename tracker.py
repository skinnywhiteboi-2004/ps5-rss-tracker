#!/usr/bin/env python3
"""Build a PS5 patch-news RSS feed from Google News RSS search results."""
import json, os, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'site'
OUT.mkdir(exist_ok=True)
GAMES = json.loads((ROOT / 'games.json').read_text(encoding='utf-8'))
BASE = os.environ.get('PAGES_URL', 'https://example.github.io/ps5-rss-tracker/').rstrip('/') + '/'
now = datetime.now(timezone.utc)
items = []
for game in GAMES:
    game = str(game).strip()
    if not game: continue
    query = f'"{game}" ("PS5" OR "PlayStation 5") ("patch notes" OR "game update" OR "new patch")'
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': query, 'hl':'en-US', 'gl':'US', 'ceid':'US:en'})
    try:
        request = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 PS5RSSTracker/1.0'})
        with urllib.request.urlopen(request, timeout=25) as response:
            root = ET.fromstring(response.read())
        for entry in root.findall('./channel/item')[:12]:
            title = (entry.findtext('title') or '').strip()
            link = (entry.findtext('link') or '').strip()
            guid = (entry.findtext('guid') or link).strip()
            date_raw = entry.findtext('pubDate') or ''
            try:
                published = parsedate_to_datetime(date_raw).astimezone(timezone.utc)
            except Exception:
                continue
            if (now-published).days > 30 or published > now: continue
            if not title or not link: continue
            items.append({'game':game, 'title':title, 'link':link, 'guid':guid, 'date':published})
        print(f'Checked {game}')
    except Exception as error:
        print(f'WARNING: Failed to check {game}: {error}')

unique = {}
for item in items:
    unique[(item['game'],item['guid'])] = item
items = sorted(unique.values(), key=lambda x:x['date'], reverse=True)[:100]
xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0"><channel>',
       '<title>My PS5 Game Patch News</title>',f'<link>{escape(BASE)}</link>',
       '<description>Game-specific PS5 patch news search results. Articles are not verified game updates.</description>',
       '<language>en-us</language>',f'<lastBuildDate>{format_datetime(now)}</lastBuildDate>']
for i in items:
    title = f"[{i['game']}] {i['title']}"
    guid = i['game']+'|'+i['guid']
    xml.extend([f'<item><title>{escape(title)}</title>',f'<link>{escape(i["link"])}</link>',
                f'<guid isPermaLink="false">{escape(guid)}</guid>',
                f'<pubDate>{format_datetime(i["date"])}</pubDate>',
                '<description>Possible PS5 patch/update coverage; verify details at the linked source.</description></item>'])
xml.append('</channel></rss>')
(OUT/'feed.xml').write_text('\n'.join(xml), encoding='utf-8')
rows = '\n'.join(f'<li><small>{i["date"].strftime("%Y-%m-%d")}</small> <strong>{escape(i["game"])}</strong> — <a href="{escape(i["link"],quote=True)}" rel="noopener noreferrer">{escape(i["title"])}</a></li>' for i in items)
html = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>My PS5 Update News</title><link rel="alternate" type="application/rss+xml" title="PS5 Patch News" href="feed.xml"><style>body{{font:16px system-ui;max-width:820px;margin:45px auto;padding:0 18px;background:#101726;color:#f1f5ff}}a{{color:#8dc5ff}}li{{padding:12px 0;border-bottom:1px solid #364155;line-height:1.6}}small{{color:#bac7dc}}.note{{color:#bac7dc}}</style><h1>🎮 My PS5 Patch News</h1><p><a href="feed.xml">Subscribe to RSS</a></p><p class="note">Tracks articles mentioning updates for your chosen games, not confirmed installed-game version changes. Last checked: {now.strftime('%Y-%m-%d %H:%M UTC')}.</p><ul>{rows or '<li>No matching news in the past 30 days, or sources were unavailable.</li>'}</ul></html>'''
(OUT/'index.html').write_text(html,encoding='utf-8')
(OUT/'.nojekyll').touch()
print(f'Generated {len(items)} articles')
