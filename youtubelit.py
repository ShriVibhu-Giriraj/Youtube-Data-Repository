import googleapiclient.discovery
import pandas as pd
import streamlit as st
from googleapiclient.errors import HttpError
from IPython.display import JSON
import pymongo
from pymongo import MongoClient


Api_key = 'AIzaSyB9_eIIdfomf0pj8w4JcGrAIXfaKlViWeQ'
api_service_name = "youtube"
api_version = "v3"
youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=Api_key)

st.sidebar.header("YouTube Data Analysis")
Ids = st.sidebar.text_input("Enter Channel ID")
#mongo-connection
client = pymongo.MongoClient("mongodb+srv://shrivibhu:ptKZ6kwxHrtmn4rM@cluster0.ujlzrwl.mongodb.net/?retryWrites=true&w=majority")

#

def get_channel_by_id(Ids):
    all_data = []
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=Ids
    )
    response = request.execute()
    for item in response['items']:
        data = {
            'channel_title': item['snippet']['title'],
            'total_video_count': item['statistics']['videoCount'],
            'subscribers': item['statistics']['subscriberCount'],
            'playlist_id': item['contentDetails']['relatedPlaylists']['uploads']
        }
        all_data.append(data)
    return all_data


def get_video_ids(playlist_ids):
    video_ids = []
  
    for playlist_id in playlist_ids:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50
        )
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')
        while next_page_token is not None:
            request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response['items']:
                video_ids.append(item['contentDetails']['videoId'])

            next_page_token = response.get('nextPageToken')

    return video_ids


def get_video_details(video_ids):
    all_video_info = []

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i+50])
        )
        response = request.execute()

        for video in response['items']:
            stats_to_keep = {'snippet': ['channelTitle', 'title'],
                             'statistics': ['viewCount', 'likeCount', 'commentCount'],
                            }
            video_info = {}
            video_info['video_id'] = video['id']

            for k in stats_to_keep.keys():
                for v in stats_to_keep[k]:
                    try:
                        video_info[v] = video[k][v]
                    except:
                        video_info[v] = None

            all_video_info.append(video_info)

    return all_video_info
#
def get_comments(video_ids):
    all_comments = []
    
    for video_id in video_ids:
        try:
            request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id
            )
            response = request.execute()
            for item in response['items']:
                comment = {
                    'comment_id': item['id'],
                    'comment': item['snippet']['topLevelComment']['snippet']['textOriginal'],
                    'comment_author': item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                }
                all_comments.append(comment)
        
        except HttpError as e:
            error = e.content.decode("utf-8")
            if "commentsDisabled" in error:
                print(f"Comments are disabled for video ID: {video_id}")
                continue  # Skip to the next iteration of the loop
            else:
                print(f"Error occurred while retrieving comments for video ID: {video_id}")
                continue  # Skip to the next iteration of the loop
    
    all_comments_df = pd.DataFrame(all_comments)
    return all_comments_df
#
def user_choice(video_details):
    db = client["mydatabase"]
    collection = db["mycollection"]
    
    for _, row in video_details.iterrows():
        video_dict = row.to_dict()
        collection.insert_one(video_dict)


if Ids:
    # Get channel details
    st.subheader("Channel Details")
    get_id = get_channel_by_id(Ids)
    st.dataframe(get_id)

    # Get video ids
    
    playlist_ids = [data['playlist_id'] for data in get_id]
    video_ids = get_video_ids(playlist_ids)
    st.dataframe(video_ids)

    # Get video details
    st.subheader("Video Details")
    video_details = pd.DataFrame(get_video_details(video_ids))
    st.dataframe(video_details)
    #button to store to the atlas
    st.write("button clicked!")
    if st.button("click me to store the values in database"):
        user_choice(video_details)        


    # get comments
    st.subheader("Comments")
    comments=get_comments(video_ids)
    st.dataframe(comments)