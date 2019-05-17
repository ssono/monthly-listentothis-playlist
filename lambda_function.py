import json
import os
import praw
import requests
import base64
import datetime

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
        12: 'December',
    }
    date = str(datetime.datetime.now()).split('-')
    m = months[(int(date[1])-1)%12]
    playlist_name = m + ' ' + date[0]
    url = "https://api.spotify.com/v1/users/"+userid+"/playlists/"
    payload = '{"name": '+'"'+playlist_name+'"'+'}'
    response = requests.request('POST', url, headers = headers, data = payload, allow_redirects=False, timeout=None)
    return response.json()['id']

def getSongUri(keywords, authorization, headers):
    keywords = keywords.replace(' ', '%20')
    url = "https://api.spotify.com/v1/search?q="+keywords+"&type=track&limit=1"
    response = requests.request('GET', url, headers = headers, allow_redirects=False, timeout=None)
    track = response.json()
    uri = track['tracks']['items'][0]['uri']
    return uri

def addSongs(playlist_id, uri_list, authorization, headers):
    uristring = ','.join(uri_list)
    uristring = uristring.replace(':', '%3A')
    url = 'https://api.spotify.com/v1/playlists/'+playlist_id+'/tracks?uris='+uristring
    response = requests.request("POST", url, headers=headers, allow_redirects=False, timeout=None)

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
    playlist_id = makePlaylist(os.environ['user_id'], authorization, headers)
    song_uris = []
    for submission in reddit.subreddit('listentothis').top(time_filter='month', limit=100):
        if len(song_uris) == 50:
            break
        t = submission.title
        t = t.split(' [')[0]
        t = t.split('(')[0]
        t = t.replace('- ', '')
        search_term = t.replace('-', '')
        try:
            song_uris.append(getSongUri(search_term, authorization, headers))
        except IndexError:
            pass
    addSongs(playlist_id, song_uris, authorization, headers)