import requests

MUSICBRAINZ_BASE = 'https://musicbrainz.org/ws/2'
COVERART_BASE = 'https://coverartarchive.org'
headers = {'User-Agent': 'MusicLibraryTest/1.0', 'Accept': 'application/json'}

def test_mb(title):
    print(f"\n--- Testing '{title}' ---")
    resp = requests.get(f'{MUSICBRAINZ_BASE}/release/', params={'query': f'release:"{title}"', 'fmt': 'json', 'limit': 1}, headers=headers)
    data = resp.json()
    if not data.get('releases'):
        print("No releases found.")
        return
        
    r = data['releases'][0]
    mbid = r['id']
    rg_id = r.get('release-group', {}).get('id')
    
    print(f"ID: {mbid}")
    print(f"Text-Rep: {r.get('text-representation')}") # Contains language
    
    # Try getting cover from release
    c_resp = requests.get(f'{COVERART_BASE}/release/{mbid}/front', allow_redirects=True)
    print(f"Cover release HTTP {c_resp.status_code}")
    
    # Try getting cover from release-group
    if rg_id:
        c_resp_rg = requests.get(f'{COVERART_BASE}/release-group/{rg_id}/front', allow_redirects=True)
        print(f"Cover release-group HTTP {c_resp_rg.status_code}")

test_mb("kyougen")
test_mb("love yourself")
test_mb("meteora")
