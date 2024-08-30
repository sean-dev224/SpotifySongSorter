import os
import base64
import json
from requests import post, get, put
from flask import Flask, request, redirect, render_template
from tabulate import tabulate

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
        "scope": "playlist-read-private playlist-modify-public playlist-modify-private"
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

class Track:
    def __init__(self, name, popularity, date, album, artist, track_uri) -> None:
        self.name = name
        self.popularity = popularity
        self.date = date
        self.album = album
        self.artist = artist
        self.track_uri = track_uri

    def __str__(self) -> str:
        return f"{self.name} by {self.artist}, {self.date}"

#sends a request to the spotify api to retrieve the user's playlist
def get_songs(access_token, url):
    url = f"{get_api_playlist_link(url)}"
    headers = {"Authorization": "Bearer " + access_token}

    result = get(url=url, headers=headers)
    json_result = json.loads(result.content)

    playlist_name = json_result["name"]
    tracks = []
    
    for i in range(len(json_result["tracks"]["items"]) - 1):
        name = json_result["tracks"]["items"][i]["track"]["name"]
        popularity = json_result["tracks"]["items"][i]["track"]["popularity"]
        date = json_result["tracks"]["items"][i]["track"]["album"]["release_date"]
        album = json_result["tracks"]["items"][i]["track"]["album"]["name"]
        artist = json_result["tracks"]["items"][i]["track"]["artists"][0]["name"]
        track_uri = json_result["tracks"]["items"][i]["track"]["uri"]

        track = Track(name, popularity, date, album, artist, track_uri)
        tracks.append(track)
    return (playlist_name, tracks)

def sort_tracks(tracks, sort_type):
    match sort_type:
        case "name":
            new_list = sorted(tracks, key=lambda x: x.name, reverse=True)
            return new_list
        
        case "popularity":
            new_list = sorted(tracks, key=lambda x: x.popularity, reverse=True)
            return new_list
        
        case "date":
            new_list = sorted(tracks, key=lambda x: x.date, reverse=True)
            return new_list
        
        case "artist":
            new_list = sorted(tracks, key=lambda x: (x.artist, x.date))
            return new_list

def listify_tracks(tracks):
    tracks_as_list = [["Track Name", "Artist", "Album", "Release Date", "Popularity Score"]]
    for x in tracks:
        tracks_as_list.append([x.name, x.artist, x.album, x.date, str(x.popularity)])
    return tracks_as_list

#default page for the website. this automatically redirects the user to spotify's authorization page
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        global playlist_url, sort_type
        playlist_url = request.form.get("playlist")
        sort_type = request.form.get("sort_type")
        return redirect(get_authorization_url())

    return render_template('index.html')

@app.route('/callback')
def callback():
    #this gets the code from the url
    code = request.args.get('code')
    global access_token
    access_token = get_access_token(code)

    if access_token:
        return redirect("/songs")
        
    else:
        return "Error: unable to retrieve access token"
    
@app.route('/songs')
def songs():
    playlist_name, tracks = get_songs(access_token, playlist_url)
    global sorted_tracks
    sorted_tracks = sort_tracks(tracks, sort_type)
    trackslist = listify_tracks(sorted_tracks)
    return render_template('songs.html', data=trackslist, playlist_name=playlist_name, sort_type=sort_type)




def main():
    app.run(port=8888, debug=True)    

if __name__ == "__main__":
    main()