import os
from flask import Flask, redirect, url_for, request, session, jsonify, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Hardcoded credentials
CLIENT_ID = '4d4dcb88bbb604f72b999ac7d64697911b'
CLIENT_SECRET = '6f66d094c8234bb4ac4f95078b40dd48'
REDIRECT_URI = 'https://spotify-music-x7iv.onrender.com/callback'  # Not used since no user auth

# Use Client Credentials for search (no user login needed)
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

@app.route('/')
def index():
    # HTML template with embedded JS for simplicity
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>StreamBeatz Spotify Integration</title>
    </head>
    <body>
        <h1>Spotify Song Search and Preview Player</h1>
        <p>Note: Due to Spotify's restrictions, only 30-second previews can be played without a Premium account. Full playback requires individual users to have Spotify Premium and authenticate, but as per your request to allow everyone without Premium, we've implemented preview playback which works for all visitors without login.</p>
        <input type="text" id="searchInput" placeholder="Search for a song">
        <button onclick="searchSongs()">Search</button>
        <div id="results"></div>
        <audio id="audioPlayer" controls></audio>
        
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
                        trackDiv.onclick = () => playPreview(track.preview_url);
                        resultsDiv.appendChild(trackDiv);
                    });
                })
                .catch(error => console.error('Search error:', error));
            }

            function playPreview(url) {
                if (!url) {
                    alert('No preview available for this track.');
                    return;
                }
                let player = document.getElementById('audioPlayer');
                player.src = url;
                player.play();
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

if __name__ == '__main__':
    app.run(debug=True)
