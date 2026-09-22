import urllib.request
import json
import traceback

def test():
    try:
        url = 'http://127.0.0.1:8000/api/tmdb/movies/634649/related'
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode('utf-8'))
            source = data.get('source_movie', {})
            print(f"Source: {source.get('title')}")
            related = data.get('related_movies', [])
            print(f"Found {len(related)} related movies.")
            for i, m in enumerate(related[:5]):
                print(f"{i+1}. {m.get('title')} - Score: {m.get('relationship_score')}")
                print(f"   Reasons: {', '.join(m.get('relationship_reasons', []))}")
    except Exception as e:
        traceback.print_exc()

if __name__ == '__main__':
    test()
