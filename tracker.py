"""Conservative verified PS4 patch RSS generator; PS5 support requires verified source."""
import json
import os
import re
import html
import datetime as dt
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'public'
OUT.mkdir(exist_ok=True)
STATE = ROOT / 'state.json'
CUSA = re.compile(r'^CUSA\d{5}$')
PPSA = re.compile(r'^PPSA\d{5}$')
BASE = 'https://skinnywhiteboi-2004.github.io/ps5-rss-tracker/'

def load_json(path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding='utf-8'))

def main():
    games = load_json(ROOT / 'games.json', {}).get('games', [])
    state = load_json(STATE, {'latest': {}, 'events': []})
    state.setdefault('latest', {})
    state.setdefault('events', [])
    errors = []
    checked = 0
    for game in games:
        if not isinstance(game, dict) or not isinstance(game.get('name'), str):
            raise ValueError('Each game must have a name and PS4/PS5 ID arrays')
        name = game['name']
        ps4ids = game.get('ps4_ids', [])
        ps5ids = game.get('ps5_ids', [])
        if not isinstance(ps4ids, list) or not isinstance(ps5ids, list):
            raise ValueError(f'{name}: IDs must be arrays')
        for ppsa in ps5ids:
            if not PPSA.fullmatch(ppsa):
                raise ValueError(f'{name}: invalid PS5 ID {ppsa!r}')
            errors.append(f'{name} ({ppsa}): PS5 automated verification not configured; skipped')
        for cusa in ps4ids:
            if not CUSA.fullmatch(cusa):
                raise ValueError(f'{name}: invalid PS4 ID {cusa!r}')
            try:
                from ps4_updates import Ps4TitleUpdate
                item = Ps4TitleUpdate(cusa)
                item.get_update()
                # Avoid inventing a version if library schema or response changes.
                version = getattr(item, 'version', None)
                if not isinstance(version, str) or not re.fullmatch(r'\d{1,3}\.\d{1,3}', version):
                    errors.append(f'{name} ({cusa}): no verifiable version from provider; skipped')
                    continue
                checked += 1
                key = f'PS4:{cusa}'
                if key not in state['latest']:
                    state['latest'][key] = version  # establish baseline without announcing old patches
                elif state['latest'][key] != version:
                    state['latest'][key] = version
                    now = dt.datetime.now(dt.timezone.utc).isoformat()
                    state['events'].insert(0, {'id': f'{key}:{version}', 'game': name, 'platform': 'PS4', 'version': version, 'date': now, 'url': f'https://www.orbispatches.com/'})
            except Exception as exc:
                errors.append(f'{name} ({cusa}): {type(exc).__name__}: {exc}')
    state['events'] = state['events'][:200]
    STATE.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    for tag, value in [('title', 'Verified PlayStation patches'), ('link', BASE), ('description', 'Confirmed version changes only; PS5 checks disabled pending verified API.')]:
        ET.SubElement(channel, tag).text = value
    for event in state['events']:
        item = ET.SubElement(channel, 'item')
        for tag, value in [('title', f"{event['game']} — {event['platform']} patch {event['version']}"), ('link', event['url']), ('guid', event['id']), ('description', f"Detected change to patch version {event['version']} for {event['platform']} title."), ('pubDate', dt.datetime.fromisoformat(event['date']).strftime('%a, %d %b %Y %H:%M:%S GMT'))]:
            ET.SubElement(item, tag).text = value
    ET.ElementTree(rss).write(OUT / 'feed.xml', encoding='utf-8', xml_declaration=True)
    status = f'Checked {checked} PS4 IDs; {len(state["events"])} saved events. PS5 checks unavailable. '
    status += ' '.join(errors) if errors else 'Add verified CUSA IDs to begin.'
    (OUT / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>PlayStation patch tracker</title><h1>PlayStation patch tracker</h1><p><a href="feed.xml">RSS feed</a></p><pre>' + html.escape(status) + '</pre>', encoding='utf-8')
    print(status)

if __name__ == '__main__':
    main()
