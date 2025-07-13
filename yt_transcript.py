import os
import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from yt_scrape import get_transcript
import json
import asyncio

class YoutubeTranscriptRetriever():
    def __init__(self, YT_API_KEY, CHANNEL_ID):
        self.YT_API_KEY = YT_API_KEY
        self.CHANNEL_ID = CHANNEL_ID
        self.UPLOAD_ID = self.get_upload_id()

    def get_upload_id(self):
        upload_id_url = f'https://www.googleapis.com/youtube/v3/channels?id={self.CHANNEL_ID}&key={self.YT_API_KEY}&part=contentDetails'
        try:
            self.UPLOAD_ID = requests.get(upload_id_url).json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        except Exception as e:
            print('Error retrieving upload ID')
            return
        return self.UPLOAD_ID

    def get_video_ids(self):
        init_vid_url = f'https://www.googleapis.com/youtube/v3/playlistItems?playlistId={self.UPLOAD_ID}&key={self.YT_API_KEY}&part=snippet&maxResults=50'
        page_details = requests.get(init_vid_url)

        vids = []
        n_video_ids = 0

        while True:
            n_video_ids += len(page_details.json()['items'])
            vids += [{'title': vid['snippet']['title'], 'videoId': vid['snippet']['resourceId']['videoId']} for vid in page_details.json()['items']]

            if 'nextPageToken' in page_details.json():
                next_page_token = page_details.json()['nextPageToken']
                page_details = requests.get(init_vid_url + f"&pageToken={next_page_token}")
            else:
                break

        return vids, n_video_ids

    def get_transcripts(self, vids, transcript_savepath):
        ts_len = 0
        num_valid_vids = 0
        # Iterate through videos in reverse order to remove invalid videos
        for i in range(len(vids) - 1, -1, -1):
            if i % 10 == 0:
                print(f'Processing video {i}')
            try:
                vid_id = vids[i]['videoId']
                # ts = YouTubeTranscriptApi.get_transcript(vids[i]['videoId'], languages=['en'])
                ts, url, is_english = asyncio.run(get_transcript(vid_id))

                if not is_english:
                    raise Exception(f'No english transcript available')
                
                print(f"Transcript Excerpt: {ts[:50]}..., Vid URL: {url}, Is English: {is_english}")
            except Exception as e:
                vids.pop(i)
                print(f'Error: {e}, Vid URL: {url}')
                continue
            # txt_formatter = TextFormatter()
            # ts_txt = txt_formatter.format_transcript(ts).replace('\n', ' ')
            vids[i]['transcript'] = ts

            ts_len += len(ts)
            num_valid_vids += 1

        with open(transcript_savepath, 'w') as file:
            json.dump(vids, file)
        
        return vids, num_valid_vids


if __name__ == '__main__':
    import sys
    # Load API keys
    load_dotenv()
    YT_API_KEY = os.getenv('YT_API_KEY')
    CHANNEL_ID = sys.argv[1]
    # CHANNEL_ID = 'UClHVl2N3jPEbkNJVx-ItQIQ' # HealthyGamerGG YT CHANNEL ID FOR TESTING PURPOSES
    transcript_savepath = sys.argv[2]

    yt_retriever = YoutubeTranscriptRetriever(YT_API_KEY, CHANNEL_ID)
    yt_retriever.get_upload_id()
    vids, _ = yt_retriever.get_video_ids()
    transcripts, _ = yt_retriever.get_transcripts(vids, transcript_savepath)
