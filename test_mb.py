import requests
import json

MUSICBRAINZ_BASE = 'https://musicbrainz.org/ws/2'
headers = {'User-Agent': 'MusicLibraryTest/1.0', 'Accept': 'application/json'}

# Test search for love yourself
resp = requests.get(f'{MUSICBRAINZ_BASE}/release/', params={'query': 'release:\"love yourself\"', 'fmt': 'json', 'limit': 5}, headers=headers)
data = resp.json()
print('SEARCH RESULTS FOR LOVE YOURSELF:')
for r in data.get('releases', []):
    print(f"ID: {r['id']}, Title: {r.get('title')}, Date: {r.get('date')}, Release Group Date: {r.get('release-group', {}).get('first-release-date')}")
