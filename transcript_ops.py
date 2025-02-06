import requests
from openai import OpenAI
import json
import matplotlib.pyplot as plt

class TranscriptProcessor():
    def __init__(self, vids=None, transcript_savepath=None):
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
    
    def save_filtered_transcripts(self, savepath):
        with open(savepath, 'w') as file:
            json.dump(self.filtered_vids, file)
        file.close()
        return


class TranscriptSummarizer(TranscriptProcessor):
    def __init__(self, vids=None, transcript_savepath=None):
        super().__init__(vids=vids, transcript_savepath=transcript_savepath)
        self.default_dev_prompt = \
            'You are a transcript summarizer, your purpose is to provide a detailed summary of a transcript without introducing any of your own bias \
            or subjectivity. Shorten the transcript while keeping all important information, including main topics, research findings, their connections \
            and importance, concrete examples demonstrated, reasoning steps, and concrete solutions. Make sure to delve into how the thought process builds \
            and how the conclusions are logically derived. Do not try to be concise. Do not interject your own opinion. Do not structure the output in any \
            way with titles or bullet points.'
    
    def summarize_transcripts(self, vids, model_name='gpt-4o-mini', dev_prompt=self.default_dev_prompt):
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
                break
            vid['summary'] = completion.choices[0].message.content

        self.filtered_vids = vids
        return vids