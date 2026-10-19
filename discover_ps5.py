"""Conservative public-page discovery of PS5 Sony update XML URLs.
Only accepts literal Sony URLs containing the configured PPSA ID.
Discovery is best-effort; some sites render links with JavaScript.
"""
import html
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SONY_URL = re.compile(r'https?://[A-Za-z0-9.-]*\.playstation\.net/[^\s"\'<>\\]+?-version\.xml', re.I)
PPSA = re.compile(r'^PPSA\d{5}$')

def fetch(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; PS5PatchRSS/1.0)'})
    with urlopen(req, timeout=18) as response:
        return response.read(2_000_000).decode('utf-8', 'replace')

def discover(title_id):
    if not PPSA.fullmatch(title_id):
        raise ValueError('Invalid PPSA ID')
    sources = [f'https://prosperopatches.com/{title_id}', f'https://www.prosperopatches.com/{title_id}']
    found = []
    diagnostics = []
    for source in sources:
        try:
            page = fetch(source)
            for candidate in (page, html.unescape(page), unquote(html.unescape(page))):
                for match in SONY_URL.finditer(candidate):
                    url = match.group(0).rstrip('.,;)')
                    parsed = urlparse(url)
                    if parsed.hostname and parsed.hostname.endswith('.playstation.net') and title_id in parsed.path.upper() and url not in found:
                        found.append(url)
        except Exception as exc:
            diagnostics.append(f'{source}: {type(exc).__name__}: {exc}')
    return found, diagnostics

def main():
    games = json.loads((ROOT / 'games.json').read_text(encoding='utf-8'))['games']
    path = ROOT / 'ps5_sources.json'
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    for game in games:
        for title_id in game.get('ps5_ids', []):
            if title_id in data and data[title_id]:
                print(f'{game["name"]} ({title_id}): already configured')
                continue
            urls, diagnostics = discover(title_id)
            if urls:
                data[title_id] = urls[0]
                print(f'{game["name"]} ({title_id}): candidate Sony URL found; validate before use')
            else:
                print(f'{game["name"]} ({title_id}): no Sony URL exposed in public HTML')
            for message in diagnostics:
                print('  ' + message)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
