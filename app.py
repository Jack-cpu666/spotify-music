import os
from flask import Flask, redirect, url_for, request, session, jsonify, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load from environment variables (set these in Render.com dashboard)
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI')  # e.g., https://your-render-app.onrender.com/callback

# Required scopes for search and playback
SCOPE = 'user-read-private user-read-email streaming user-read-playback-state user-modify-playback-state user-read-currently-playing'

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=".cache"  # Cache for token, but in Render, use a persistent path if needed
)

@app.route('/')
def index():
    token_info = session.get('token_info')
    if token_info:
        # Refresh if needed
        if sp_oauth.is_token_expired(token_info):
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info
        token = token_info['access_token']
    else:
        token = None

    # HTML template with embedded JS for simplicity
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>StreamBeatz Spotify Integration</title>
        <script src="https://sdk.scdn.co/spotify-player.js"></script>
    </head>
    <body>
        <h1>Spotify Song Search and Player</h1>
        {% if not token %}
            <a href="/login">Login with Spotify</a>
            <p>Note: Full playback requires a Spotify Premium account. This app allows visitors to link their own Spotify accounts for playback.</p>
        {% else %}
            <input type="text" id="searchInput" placeholder="Search for a song">
            <button onclick="searchSongs()">Search</button>
            <div id="results"></div>
            <div id="playerStatus">Player initializing...</div>
        {% endif %}
        
        <script>
            let token = "{{ token }}";
            let deviceId = null;
            let player = null;

            if (token) {
                window.onSpotifyWebPlaybackSDKReady = () => {
                    player = new Spotify.Player({
                        name: 'StreamBeatz Player',
                        getOAuthToken: cb => { cb(token); },
                        volume: 0.5
                    });

                    player.addListener('ready', ({ device_id }) => {
                        deviceId = device_id;
                        document.getElementById('playerStatus').innerText = 'Player ready! Device ID: ' + device_id;
                    });

                    player.addListener('not_ready', ({ device_id }) => {
                        document.getElementById('playerStatus').innerText = 'Player offline: ' + device_id;
                    });

                    player.addListener('player_state_changed', state => {
                        console.log('Player state changed:', state);
                    });

                    player.connect();
                };

                function searchSongs() {
                    let query = document.getElementById('searchInput').value;
                    fetch('/search?q=' + encodeURIComponent(query), {
                        headers: { 'Authorization': 'Bearer ' + token }
                    })
                    .then(response => response.json())
                    .then(data => {
                        let resultsDiv = document.getElementById('results');
                        resultsDiv.innerHTML = '';
                        data.forEach(track => {
                            let trackDiv = document.createElement('div');
                            trackDiv.innerText = track.name + ' - ' + track.artists[0].name;
                            trackDiv.style.cursor = 'pointer';
                            trackDiv.onclick = () => playTrack(track.uri);
                            resultsDiv.appendChild(trackDiv);
                        });
                    })
                    .catch(error => console.error('Search error:', error));
                }

                function playTrack(uri) {
                    if (!deviceId) {
                        alert('Player not ready yet.');
                        return;
                    }
                    fetch('https://api.spotify.com/v1/me/player/play?device_id=' + deviceId, {
                        method: 'PUT',
                        body: JSON.stringify({ uris: [uri] }),
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer ' + token
                        }
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Playback failed');
                        }
                        console.log('Playing:', uri);
                    })
                    .catch(error => console.error('Playback error:', error));
                }
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, token=token or '')

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect('/')

@app.route('/search')
def search():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'error': 'No token'}), 401
    sp = spotipy.Spotify(auth=token)
    q = request.args.get('q')
    if not q:
        return jsonify({'error': 'No query'}), 400
    results = sp.search(q=q, type='track', limit=10)
    tracks = [{
        'name': item['name'],
        'artists': item['artists'],
        'uri': item['uri']
    } for item in results['tracks']['items']]
    return jsonify(tracks)

if __name__ == '__main__':
    app.run(debug=True)
