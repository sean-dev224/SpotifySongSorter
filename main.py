import os
import base64
import json
from requests import post, get, put
from flask import Flask, request, redirect, render_template

#dotenv makes it easy to load env files, which store environment variables.
from dotenv import load_dotenv
load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")

app = Flask(__name__)

def get_authorization_url(): #makes the url to prompt a user to authorize this program

    auth_url = "https://accounts.spotify.com/authorize"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": "playlist-read-private"
    }
    url_params = "&".join([f"{key}={value}" for key, value in params.items()])
    return f"{auth_url}?{url_params}"

def get_access_token(code): #gives the code from spotify's url in order to get the access token
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode()
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
    result = post(url, headers=headers, data=data)
    return result.json().get('access_token')

def get_api_playlist_link(url): #makes the api url from the user-entered url
    playlist_id = url.replace("https://open.spotify.com/playlist/", "")

    return "https://api.spotify.com/v1/playlists/" + playlist_id

#sends a request to the spotify api to retrieve the user's playlist
def get_top_songs(access_token, url):
    url = f"{get_api_playlist_link(url)}"
    headers = {"Authorization": "Bearer " + access_token}

    result = get(url=url, headers=headers)
    json_result = json.loads(result.content)

    name = json_result["name"]
    tracks = []
    for i in range(len(json_result["tracks"]["items"])):
        tracks.append((json_result["tracks"]["items"][i]["track"]["name"], 
                       json_result["tracks"]["items"][i]["track"]["popularity"]))
        
    return sorted(tracks, key=lambda track: track[1], reverse=True)

#default page for the website. this automatically redirects the user to spotify's authorization page
@app.route('/', methods=['POST', 'GET'])
@app.route('/home')
def index():

    if request.method == 'POST':
        global playlist_url 
        playlist_url = request.form.get("playlist")
        return redirect(get_authorization_url())

    return render_template('index.html')

@app.route('/callback')
def callback():
    #this gets the code from the url
    code = request.args.get('code')
    access_token = get_access_token(code)

    if access_token:
        song_list = get_top_songs(access_token, playlist_url)
        return render_template('songs.html', data=song_list)
    else:
        return "Error: unable to retrieve access token"



if __name__ == "__main__":
    app.run(port=8888, debug=True)