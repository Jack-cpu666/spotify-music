import os
from flask import Flask, jsonify, request, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pytube import Search

app = Flask(__name__)

# Hardcoded credentials
CLIENT_ID = '4d4dcb88bb6047f2b999ac7d6497811b'
CLIENT_SECRET = '6f66d094c8234bb4ac4f95078b40dd48'

# Use Client Credentials for search (no user login needed)
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

@app.route('/')
def index():
    # HTML template with embedded JS for simplicity
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>StreamBeatz Spotify Integration with Full Playback</title>
    </head>
    <body>
        <h1>Spotify Song Search and Full Player</h1>
        <p>Note: Searches use Spotify API. Full playback is provided via YouTube embeds (legal way around Spotify's Premium restriction for API playback). This allows anyone to play full tracks without Spotify Premium.</p>
        <input type="text" id="searchInput" placeholder="Search for a song">
        <button onclick="searchSongs()">Search</button>
        <div id="results"></div>
        <div id="player" style="margin-top: 20px;"></div>
        
        <script>
            function searchSongs() {
                let query = document.getElementById('searchInput').value;
                fetch('/search?q=' + encodeURIComponent(query))
                .then(response => response.json())
                .then(data => {
                    let resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = '';
                    data.forEach(track => {
                        let trackDiv = document.createElement('div');
                        trackDiv.innerText = track.name + ' - ' + track.artists[0].name;
                        trackDiv.style.cursor = 'pointer';
                        trackDiv.onclick = () => playTrack(track.name, track.artists[0].name);
                        resultsDiv.appendChild(trackDiv);
                    });
                })
                .catch(error => console.error('Search error:', error));
            }

            function playTrack(name, artist) {
                fetch('/get_youtube?url=' + encodeURIComponent(name + ' ' + artist + ' official audio'))
                .then(response => response.json())
                .then(data => {
                    if (data.video_id) {
                        let playerDiv = document.getElementById('player');
                        playerDiv.innerHTML = `<iframe width="560" height="315" src="https://www.youtube.com/embed/${data.video_id}?autoplay=1" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`;
                    } else {
                        alert('No YouTube video found.');
                    }
                })
                .catch(error => console.error('YouTube search error:', error));
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/search')
def search():
    q = request.args.get('q')
    if not q:
        return jsonify({'error': 'No query'}), 400
    results = sp.search(q=q, type='track', limit=10)
    tracks = [{
        'name': item['name'],
        'artists': item['artists'],
        'preview_url': item['preview_url']
    } for item in results['tracks']['items']]
    return jsonify(tracks)

@app.route('/get_youtube')
def get_youtube():
    query = request.args.get('url')
    if not query:
        return jsonify({'error': 'No query'}), 400
    try:
        s = Search(query)
        if s.results:
            video_id = s.results[0].video_id
            return jsonify({'video_id': video_id})
        else:
            return jsonify({'video_id': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
