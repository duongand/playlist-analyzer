import os
import sys
import spotipy
import spotipy.util as util
from csv import DictReader, DictWriter

import json

def currentSong(sp):
    '''
    The function pulls the current playing or paused song on the user's spotify client
    Input: Spotipy client
    Output: The name of the song currently playing
    '''

    current = sp.current_user_playing_track()['item']['name'] # Extracting current song from current user from JSON data

    return current

def userPlaylists(sp):
    '''
    The function pulls all the information of playlists saved by the user.
    Input: Spotipy Client
    Output: Name and Associated ID of the playlists
    '''

    playlist_list = [] # Initialized list to compile names from current user
    playlists = sp.current_user_playlists() # JSON data of every playlist from user
    
    for item in playlists['items']: # Iterating through each playlist from JSON data
        
        n_playlist = {'name' : item['name'], 'id' : item['id']} # Extracting name and associated id of playlist
        playlist_list.append(n_playlist) # Compiling name and id of playlist of user

    return playlist_list

def playlist_id(playlist_name, playlist_list):
    '''
    The function searches for the interested playlist and checks user's playlist list to find the associated id
    Input: Playlist Name, Playlist List
    Output: Associated Playlist ID
    '''
    id = '' # ID is blank if searched playlist is not found

    for item in playlist_list: # For each playlist in the playlist list
        if item['name'] == playlist_name: # Check if the pulled playlist is the searched playlist
            id = item['id'] # If true, set id to playlist id
    
    return id

def playlistTracks(sp, playlist_id):
    '''
    The function pulls a list of tracks from the specified playlist id
    Input: Spotipy Client, Playlist ID
    Output: List of Tracks
    '''
    compiled_info = [] # Initialized blank list

    current_pulled_tracks = sp.playlist_tracks(playlist_id) # Pulled full details of the tracks within the playlist
    unfiltered_tracks = current_pulled_tracks['items'] # Extracts individual tracks from 'item's key

    while current_pulled_tracks['next']: # 'playlist_tracks' returns a paginated result with 100 result limit; if 'next' pertains, iterate through pages
        current_pulled_tracks = sp.next(current_pulled_tracks) # Pulls the next page of results
        unfiltered_tracks.extend(current_pulled_tracks['items']) # Appends results to unfiltered tracklist

    tracks = [item['track'] for item in unfiltered_tracks] # Extract 'track' key from each individual result

    for track in tracks: # Iterate through each track to extract interested attributes
        temp = {} # Temp dictionary

        temp['name'] = track['name'] # Track name
        temp['artist'] = track['artists'][0]['name'] # Artist name
        temp['album'] = track['album']['name'] # Album name
        temp['release_date'] = track['album']['release_date'] # Release date of track
        temp['duration_ms'] = track['duration_ms'] # Duration of track

        compiled_info.append(temp) # Append dictionary to running compiling list

    return compiled_info

def exportTable(track_list, playlist_name):
    '''
    The function takes a compiled and filtered list of a playlist to write into a csv
    Input: Correctly Formatted Track List, Playlist Name
    Output: .csv File of Playlist with Attributes
    '''
    file_name = 'playlist_%s.csv' % playlist_name # Formatting of file name
    field_names = ['name', 'artist', 'album', 'release_date', 'duration_ms'] # Headers of extracted keys

    with open(file_name, 'w', newline='') as csvfile: # Writes a new .csv file 
        writer = DictWriter(csvfile, fieldnames=field_names)

        writer.writeheader()
        writer.writerows(track_list)

if __name__ == '__main__':
    if len(sys.argv) > 1: # In the terminal, pass a username
        username = sys.argv[1]
    else: # If username is not provided, the program terminates
        print("You need a username!")
        sys.exit()

    SPOTIPY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
    SPOTIPY_REDIRECT_URI = 'http://localhost:8888'

    scope = 'user-read-currently-playing'
    token = util.prompt_for_user_token(username, scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI)

    if token:
        sp = spotipy.Spotify(auth=token)
    else:
        print('Invalid token for', username)

    PLAYLIST_NAME = 'na'

    playlist_list = userPlaylists(sp)
    id = playlist_id(PLAYLIST_NAME, playlist_list)
    na_tracks = playlistTracks(sp, id)
    exportTable(na_tracks, PLAYLIST_NAME)