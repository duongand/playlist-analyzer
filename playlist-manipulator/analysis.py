import sys
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import spotipy.util as util
from csv import DictReader, DictWriter
import time
import json

def currentSong(sp):
    '''
    The function pulls the current playing or paused song on the user's spotify client
    Input: Spotipy client
    Output: Attributes related to the song that could pertain to our analysis
    '''
    song = {}
    current = sp.current_user_playing_track()['item'] # Extracting current song from current user from JSON data

    song['name'] = current['name'] # Track name
    song['artist'] = current['artists'][0]['name'] # Artist name
    song['album'] = current['album']['name'] # Album name
    song['release_date'] = current['album']['release_date'] # Release date of track
    song['duration_ms'] = current['duration_ms'] # Duration of track
    song['id'] = current['id'] # ID of track
    song['play_count'] = 0 # Play count for analysis purposes

    return song

def recentSong(sp):
    '''
    The function pulls information regarding the user's latest played track
    Input: Spotipy client
    Output: Attributes of last played song
    '''
    song = {}
    recent = sp.current_user_recently_played(1)['items'][0]

    song['name'] = recent['track']['name'] # Track name
    song['artist'] = recent['track']['artists'][0]['name'] # Artist name
    song['album'] = recent['track']['album']['name'] # Album name
    song['release_date'] = recent['track']['album']['release_date'] # Release date of track
    song['duration_ms'] = recent['track']['duration_ms'] # Duration of track
    song['id'] = recent['track']['id'] # ID of track
    song['played_at'] = recent['played_at'] # Date 
    song['play_count'] = 0 # Play count for analysis purposes

    return song

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
        temp['id'] = track['id'] # ID of track
        temp['play_count'] = 0 # Play count for analysis purposes

        compiled_info.append(temp) # Append dictionary to running compiling list

    return compiled_info

def playCount(sp, playlist, n=50):
    '''
    The function takes a list of tracks from a playlist and counts the amount of times a track is played within a listening session
    Input: Listening playlist, Spotipy client, n=number of tracks updated
    Output: Playlist with counted play count
    '''
    temp = {'id' : 'abc'} # Temporary variable to compare recent song
    count =  0 # Count of number of tracks updated

    while True: 
        recent = recentSong(sp) # Retrieves attributes of previously played songs

        if temp['id'] != recent['id']: # Compares the 'temp' or previous song to 'new' previous song
            
            recent_index = search(recent['id'], playlist) # Searches for the index of the song within the playlist

            if recent_index != -1: # If index is -1, then the song is not within the playlist
                temp = recent # Replaces the 'temp' song with most recently played song
                playlist[recent_index]['play_count'] += 1 # Adds one to play count to associated song
                count += 1 # Increase count of number of tracks updated
    
        if count > n: 
            break
        
        print(count)
        time.sleep(90) # Time delay to prevent script from running unnecessarily quick, 90 seconds

    return playlist 

def search(song_id, playlist):
    '''
    The function searchs thorugh the playlist to find the index of the searched song
    Input: Song id, Playlist tracks
    Output: Index of searched song within playlist
    '''
    index = -1 # Initiliazed value of -1 to indicate false if not found

    for i in range(0, len(playlist)):
        if playlist[i]['id'] == song_id:
            index = i

    return index 

def exportTable(track_list, playlist_name):
    '''
    The function takes a compiled and filtered list of a playlist to write into a csv
    Input: Correctly Formatted Track List, Playlist Name
    Output: .csv File of Playlist with Attributes
    '''
    file_name = 'playlist_%s.csv' % playlist_name # Formatting of file name
    field_names = ['name', 'artist', 'album', 'release_date', 'duration_ms', 'id', 'play_count'] # Headers of extracted keys

    with open(file_name, 'w', newline='', encoding='utf-8') as csvfile: # Writes a new .csv file, encoding set to 'utf-8' for special characters
        writer = DictWriter(csvfile, fieldnames=field_names)

        writer.writeheader()
        writer.writerows(track_list)

if __name__ == '__main__':
    if len(sys.argv) > 1: # In the terminal, pass a username
        username = sys.argv[1]
    else: # If username is not provided, the program terminates
        print("You need a username!")
        sys.exit()

    scope = 'user-read-currently-playing'
    n = 100

    # The code block below allows for long-running application of the Spotify API 
    client_credentials_manager = SpotifyClientCredentials()
    auth_manager = SpotifyOAuth(username=username, scope=scope)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth_manager=auth_manager)

    PLAYLIST_NAME = 'unorganized'
    current_song = currentSong(sp)
    recent_song = recentSong(sp)


    playlist_list = userPlaylists(sp)
    id = playlist_id(PLAYLIST_NAME, playlist_list)
    playlist_tracks = playlistTracks(sp, id)
    counter_playlist = playCount(sp, playlist_tracks, n)
    exportTable(counter_playlist, PLAYLIST_NAME)