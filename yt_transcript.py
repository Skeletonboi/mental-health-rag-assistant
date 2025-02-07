import os
import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import json

class YoutubeTranscriptRetriever():
    def __init__(self, YT_API_KEY, CHANNEL_ID):
        self.YT_API_KEY = YT_API_KEY
        self.CHANNEL_ID = CHANNEL_ID
        self.UPLOAD_ID = self.get_upload_id()

    def get_upload_id(self):
        upload_id_url = f'https://www.googleapis.com/youtube/v3/channels?id={self.CHANNEL_ID}&key={self.YT_API_KEY}&part=contentDetails'
        try:
            UPLOAD_ID = requests.get(upload_id_url).json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        except Exception as e:
            print('Error retrieving upload ID')
        return UPLOAD_ID

    def get_video_ids(self):
        init_vid_url = f'https://www.googleapis.com/youtube/v3/playlistItems?playlistId={self.UPLOAD_ID}&key={self.YT_API_KEY}&part=snippet&maxResults=50'
        page_details = requests.get(init_vid_url)

        vids = []
        n_video_ids = len(page_details.json()['items'])
        vids += [{'title': vid['snippet']['title'], 'videoId': vid['snippet']['resourceId']['videoId']} for vid in x.json()['items']]

        while 'nextPageToken' in page_details.json():
            next_page_token = page_details.json()['nextPageToken']
            page_details = requests.get(init_vid_url + f"&pageToken={next_page_token}")
            n_video_ids += len(page_details.json()['items'])
            vids += [{'title': vid['snippet']['title'], 'videoId': vid['snippet']['resourceId']['videoId']} for vid in x.json()['items']]
        return vids, n_video_ids

    def get_transcripts(self, vids, transcript_savepath):
        ts_len = 0
        num_valid_vids = 0
        # Iterate through videos in reverse order to remove invalid videos
        for i in range(len(vids) - 1, -1, -1):
            if i % 10 == 0:
                print(f'Processing video {i}')
            try:
                ts = YouTubeTranscriptApi.get_transcript(vids[i]['videoId'], languages=['en'])
            except Exception as e:
                vids.pop(i)
                continue
            txt_formatter = TextFormatter()
            ts_txt = txt_formatter.format_transcript(ts).replace('\n', ' ')
            vids[i]['transcript'] = ts_txt

            ts_len += len(ts_txt)
            num_valid_vids += 1

        with open(transcript_savepath, 'w') as file:
            json.dump(vids, file)
        
        return vids, num_valid_vids


if __name__ == '__main__':
    # Load API keys
    load_dotenv()
    YT_API_KEY = os.getenv('YT_API_KEY')
    CHANNEL_ID = 'UClHVl2N3jPEbkNJVx-ItQIQ'

    yt_transcript_retriever = YoutubeTranscriptRetriever(YT_API_KEY, CHANNEL_ID)
