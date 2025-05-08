import os
import requests
from openai import OpenAI
import json
import matplotlib.pyplot as plt
from dotenv import load_dotenv

class TranscriptProcessor():
    def __init__(self, **transcripts):
        vids = transcripts.get('vids', None)
        transcript_savepath = transcripts.get('transcript_savepath', None)

        if not vids and not transcript_savepath:
            raise Exception('No transcripts or savepath provided')

        if transcript_savepath:
            with open(transcript_savepath, 'r') as file:
                self.vids = json.load(file)
            file.close()
        else:
            self.vids = vids
            
        self.filtered_vids = vids
    
    def remove_missing_transcripts(self, vids):
        self.filtered_vids = []
        for i, vid in enumerate(vids):
            if 'transcript' in vid:
                self.filtered_vids.append(vid)
            else:
                print("Missing transcript (likely YT Short)", vid['title'])
        return self.filtered_vids
    
    def filter_transcripts(self, vids, bounds=(0, float('inf'))):
        self.filtered_vids = []
        for i, vid in enumerate(vids):
            vid['length'] = len(vid['transcript'])
            if bounds[0] < vid['length'] < bounds[1]:
                self.filtered_vids.append(vid)
        # PLOTTING STATISTICS
        # self.filtered_vids = sorted(self.filtered_vids, key=lambda x: x[1])
        # plt.hist([vid['length'] for vid in self.filtered_vids], bins=50)
        # plt.savefig('transcript_lengths.png')
        return self.filtered_vids
    
    def save_to_file(self, savepath, vids=None):
        if not vids:
            vids = self.filtered_vids
        with open(savepath, 'w') as file:
            json.dump(vids, file)
        file.close()
        return


class TranscriptSummarizer(TranscriptProcessor):
    def __init__(self, **transcripts):
        super().__init__(**transcripts)
        self.default_dev_prompt = \
            'You are a transcript summarizer, your purpose is to provide a detailed summary of a transcript without introducing any of your own bias \
            or subjectivity. Shorten the transcript while keeping all important information, including main topics, research findings, their connections \
            and importance, concrete examples demonstrated, reasoning steps, and concrete solutions. Make sure to delve into how the thought process builds \
            and how the conclusions are logically derived. Do not try to be concise. Do not interject your own opinion. Do not structure the output in any \
            way with titles or bullet points.'
    
    def summarize_transcripts(self, vids, model_name='gpt-4o-mini', dev_prompt=None):
        client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))

        if not dev_prompt:
            dev_prompt = self.default_dev_prompt
        for i, vid in enumerate(vids):
            print('Processing video ', i, vid['title'])
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {'role': 'developer', 'content': dev_prompt},
                        {'role': 'user', 'content': vid['transcript']}
                    ]
                )
            except:
                print('Failed to process video ', i)
                continue
            vid['summary'] = completion.choices[0].message.content

        self.filtered_vids = vids
        return vids
    
if __name__ == '__main__':
    import sys
    load_dotenv()
    transcript_savepath = sys.argv[1]
    new_savepath = sys.argv[2]

    ts_operator = TranscriptSummarizer(transcript_savepath=transcript_savepath)

    vids = ts_operator.remove_missing_transcripts(ts_operator.vids)
    vids = ts_operator.filter_transcripts(vids)
    summaries = ts_operator.summarize_transcripts(vids)
    ts_operator.save_to_file(new_savepath, summaries) 
