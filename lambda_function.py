import json
import os
import praw
import requests
import base64
import datetime
import re

def isDuplicate(userid, authorization, headers):
    months = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        0: 'December',
    }

    date = str(datetime.datetime.now()).split('-')
    m = months[(int(date[1])-1)%12]
    yr = date[0]
    if m == 'January':
        yr = str(int(date[0])-1)
    playlist_name = m + ' ' + yr
    url = "https://api.spotify.com/v1/users/"+userid+"/playlists/"
    response = requests.request('GET', url, headers = headers, allow_redirects=False, timeout=None)
    playlists = response.json()
    for item in playlists['items']:
        if item['name'] == playlist_name:
            return True
    return False

def makePlaylist(userid, authorization, headers):
    months = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        0: 'December',
    }
    date = str(datetime.datetime.now()).split('-')
    m = months[(int(date[1])-1)%12]
    yr = date[0]
    if m == 'January':
        yr = str(int(date[0])-1)
    playlist_name = m + ' ' + yr
    url = "https://api.spotify.com/v1/users/"+userid+"/playlists/"
    payload = '{"name": '+'"'+playlist_name+'"'+'}'
    response = requests.request('POST', url, headers = headers, data = payload, allow_redirects=False, timeout=None)
    return response.json()['id']

def getSongUri(keywords, authorization, headers):
    keywords = keywords.replace(' ', '%20')
    url = "https://api.spotify.com/v1/search?q="+keywords+"&type=track&limit=1"
    response = requests.request('GET', url, headers = headers, allow_redirects=False, timeout=None)
    track = response.json()
    try:
        uri = track['tracks']['items'][0]['uri']
        return uri
    except KeyError:
        pass

def addSongs(playlist_id, uri_list, authorization, headers):
    uristring = ','.join(uri_list)
    uristring = uristring.replace(':', '%3A')
    url = 'https://api.spotify.com/v1/playlists/'+playlist_id+'/tracks?uris='+uristring
    response = requests.request("POST", url, headers=headers, allow_redirects=False, timeout=None)
    
def copySongs(from_id, to_id, authorization, headers):
    url = "https://api.spotify.com/v1/playlists/"+from_id+"/tracks"
    fromTracks = requests.request('GET', url, headers=headers, allow_redirects=False, timeout=None).json()['items']
    fromTracksUris = []
    
    for track in fromTracks:
        fromTracksUris.append(track['track']['uri'])
        
    addSongs(to_id, fromTracksUris, authorization, headers)
    
def clearLatest(top_50_id, authorization, headers):
    url = "https://api.spotify.com/v1/playlists/"+top_50_id+"/tracks"
    
    latestTracks = requests.request('GET', url, headers=headers, allow_redirects=False, timeout=None)
    latestTracks = latestTracks.json()['items']
    latestTracksUris = []
    
    for track in latestTracks:
        latestTracksUris.append({"uri": track['track']['uri']})
        
    payload = {"tracks": latestTracksUris}
    payload = json.dumps(payload)
    deleteUrl = 'https://api.spotify.com/v1/playlists/'+top_50_id+'/tracks'
    response = requests.request("DELETE", deleteUrl, headers=headers, data=payload, allow_redirects=False, timeout=None)
        
    

def lambda_handler(event, context):
    #Reddit api auth
    r_client_id = os.environ['r_client_id']
    r_client_secret = os.environ['r_client_secret']
    user_agent = os.environ['user_agent']

    reddit = praw.Reddit(client_id=r_client_id,
                         client_secret=r_client_secret,
                         user_agent=user_agent)

    #Spotify API auth
    s_client_id = os.environ['s_client_id']
    s_client_secret = os.environ['s_client_secret']
    refresh_token = os.environ['refresh_token']
    prep = s_client_id+':'+s_client_secret
    client_credentials = str(base64.b64encode(prep.encode('utf-8')))
    client_credentials = client_credentials[2:-1]
    user_id = os.environ['user_id']
    top_50_id = os.environ['top_50_id']

    #refresh credentials
    url = 'https://accounts.spotify.com/api/token'
    payload = {'grant_type':'refresh_token','refresh_token':refresh_token}
    headers = {
      'Authorization': 'Basic '+client_credentials
    }
    response = requests.request('POST', url, headers = headers, data = payload, allow_redirects=False, timeout=None)
    response_as_dict = response.json()

    #global stuff
    authorization = "Bearer "+response_as_dict['access_token']
    headers = {
      "Authorization": authorization,
      "Content-Type": "application/json",
      "Accept": "application/json"
    }

    #actual work
    
    if isDuplicate(user_id, authorization, headers):
        return
    
    #Create the new historical playlist
    playlist_id = makePlaylist(user_id, authorization, headers)
    
    #copy songs from latest to historical
    # copySongs(top_50_id, playlist_id, authorization, headers)
    
    #clear top 50
    clearLatest(top_50_id, authorization, headers)
    
    #refill top 50
    song_uris = []
    for submission in reddit.subreddit('listentothis').top(time_filter='month', limit=150):
        if len(song_uris) == 50:
            break
        t = submission.title
        t = t.split(' [')[0]
        t = re.sub("\([^\)]+\)", "", t)
        t = re.sub("(\u2013|\u2014|-|\")", ' ', t)
        search_term = t
        try:
            songUri = getSongUri(search_term, authorization, headers)
            if songUri:
                song_uris.append(songUri)
        except IndexError:
            pass
        
    addSongs(top_50_id, song_uris, authorization, headers)
    addSongs(playlist_id, song_uris, authorization, headers)
    
    
