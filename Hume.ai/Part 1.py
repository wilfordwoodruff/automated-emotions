from SplitLettersandJournalsbyDate import download_and_split_by_date
import pandas as pd
import os
import time
import zipfile
from hume import HumeBatchClient
from hume.models.config import LanguageConfig


full_date_api = download_and_split_by_date()


# Formats text
full_date_api['FixedText'] = (full_date_api['text'].str.replace("<.*?>",repl='',regex=True)
           .str.replace("\[\[.*\|",repl='',regex=True)
           .str.replace(']','').str.replace('[','')
           .str.replace('\n',' ')
           .str.replace('\u25c7','')
           .str.replace('\u25ca','')
           .str.replace('\u2b26','')
           .str.replace('\u0151','')
           .str.replace('\u04d0','')
           .str.replace('\u014d','')
           .str.replace('\u25a0','')
           .str.replace('&amp;','and')
)
full_date_api = full_date_api[pd.notna(full_date_api['FixedText'])].head(n=6)


#I'm hesitant to set an index, because I can't guarantee they'll always
# be in the same order. So instead of a key, we use the text directly
already_run = pd.read_csv('All_Hume_Results.csv')

#Add back the Job IDs and emotion results of what's already happened

not_yet_run = full_date_api.query("FixedText not in @already_run['FixedText']")

not_yet_run[['Job ID','Admiration', 'Adoration', 'Aesthetic Appreciation',
       'Amusement', 'Anger', 'Annoyance', 'Anxiety', 'Awe', 'Awkwardness',
       'Boredom', 'Calmness', 'Concentration', 'Confusion', 'Contemplation',
       'Contempt', 'Contentment', 'Craving', 'Determination', 'Disappointment',
       'Disapproval', 'Disgust', 'Distress', 'Doubt', 'Ecstasy',
       'Embarrassment', 'Empathic Pain', 'Enthusiasm', 'Entrancement', 'Envy',
       'Excitement', 'Fear', 'Gratitude', 'Guilt', 'Horror', 'Interest', 'Joy',
       'Love', 'Nostalgia', 'Pain', 'Pride', 'Realization', 'Relief',
       'Romance', 'Sadness', 'Sarcasm', 'Satisfaction', 'Desire', 'Shame',
       'Surprise (negative)', 'Surprise (positive)', 'Sympathy', 'Tiredness',
       'Triumph']] = None
docs_to_run = pd.concat([already_run,not_yet_run],ignore_index=True)
docs_to_run.to_csv('All_Hume_Results.csv',index=False)
#docs_to_run = full_date_api.set_index('FixedText').merge(right=already_run.set_index('FixedText').drop(columns=['UUID','Date']),how='left').reset_index()
# PART 2: START RUNNING JOBS
hume_api_key = os.getenv('HUME_WWP_API')
client = HumeBatchClient(hume_api_key)

def HumePerPage(text):
    config = LanguageConfig(sentiment={},granularity='conversational_turn',identify_speakers=False)
    job = client.submit_job(urls=[], configs=[config], text=[text])
    print("Job", str(job)," saved. Waiting for next", job)
    job_str = str(job).split(sep='"')[1]
    return job_str

#Run only on the rows that don't have a JOB ID value
#TO DO: error prevention from Hume, so we don't have to keep saving the document
rows_to_run = docs_to_run[pd.isna(docs_to_run['Job ID'])].index.to_list()
for index in rows_to_run:
    docs_to_run = pd.read_csv('All_Hume_Results.csv')
    docs_to_run.loc[index,'Job ID'] = HumePerPage(docs_to_run['FixedText'].iloc[index])
    docs_to_run.to_csv('All_Hume_Results.csv',index=False)
