#%%
'''
Might be best as Jupyter file, because of intermediate steps
1. Get New full api rip from the website
2. compare to original and remove matching UUIDs
3. Run date matcher, returning a longer dataset of each day's entry
4. Group into chunks, push to Github
5. Get Hume Job IDs
6. After waiting, get all results
7. Run the after parts
8. Add onto the pre-existing Date and Entry results
'''
from SplitLettersandJournalsbyDate import download_and_split_by_date
import pandas as pd
import os
import time
import zipfile
from hume import HumeBatchClient
from hume.models.config import LanguageConfig

#%%

full_date_api = download_and_split_by_date()

#already_run_id = pd.read_csv("already run by uuid.csv")
#already_run_date = pd.read_csv('already run by date.csv')
#needs_results = full_date_api.query("UUID not in @already_run_id['UUID']")
#needs_results.head()

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
full_date_api = full_date_api[pd.notna(full_date_api['FixedText'])]

#%%

#full_date_api.to_csv('New Entries to Match with Hume.csv')

# PART 2: START RUNNING JOBS
hume_api_key = os.getenv('HUME_WWP_API')
full_date_api['Job ID'] = ''
full_date_api.head(n=2).to_csv('All_Saved_Hume_IDs.csv',index=False)
client = HumeBatchClient(hume_api_key)

def HumePerPage(text):
    config = LanguageConfig(sentiment={},granularity='conversational_turn',identify_speakers=False)
    job = client.submit_job(urls=[], configs=[config], text=[text])
    print("Job", str(job)," saved. Waiting for next", job)
    job_str = str(job).split(sep='"')[1]
    return job_str

# This seemed like the best way to save it. Just adjust the index values if you have to restart 
START_ROW = 0
END_ROW = len(full_date_api.head(n=2))
for index in range(START_ROW,END_ROW):
    full_date_api = pd.read_csv('All_Saved_Hume_IDs.csv')
    full_date_api.loc[index,'Job ID'] = HumePerPage(full_date_api['FixedText'].iloc[index])
    full_date_api.to_csv('All_Saved_Hume_IDs.csv',index=False)

time.sleep(30)

#Sometimes it queues pages without explanation, so run this a couple hours later just in case

#needs_results = pd.read_csv('New Entries to Match with Hume.csv')
#full_date_api = pd.read_csv('Hume_IDs.csv')['0'].tolist()
#%%

emotions = ['Admiration', 'Adoration', 'Aesthetic Appreciation',
       'Amusement', 'Anger', 'Annoyance', 'Anxiety', 'Awe', 'Awkwardness',
       'Boredom', 'Calmness', 'Concentration', 'Confusion', 'Contemplation',
       'Contempt', 'Contentment', 'Craving', 'Determination', 'Disappointment',
       'Disapproval', 'Disgust', 'Distress', 'Doubt', 'Ecstasy',
       'Embarrassment', 'Empathic Pain', 'Enthusiasm', 'Entrancement', 'Envy',
       'Excitement', 'Fear', 'Gratitude', 'Guilt', 'Horror', 'Interest', 'Joy',
       'Love', 'Nostalgia', 'Pain', 'Pride', 'Realization', 'Relief',
       'Romance', 'Sadness', 'Sarcasm', 'Satisfaction', 'Desire', 'Shame',
       'Surprise (negative)', 'Surprise (positive)', 'Sympathy', 'Tiredness',
       'Triumph']

def job_to_results(row):
    client.get_job(row['Job ID']).download_artifacts(f"SectionstoRun/wwp{row['Job ID']}.zip")
    zip_file_path = f'SectionstoRun/wwp{row["Job ID"]}.zip'
    # Specify the path to the CSV file within the zip folder
    csv_file_path_within_zip = f'text-0-file/csv/1/language.csv' 
    # Extract the CSV file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extract(member=csv_file_path_within_zip)

    return pd.read_csv(csv_file_path_within_zip)[emotions].values[0].tolist()

full_date_api[emotions] = full_date_api.apply(job_to_results, axis=1, result_type='expand')

full_date_api.to_csv('Complete Detailed Hume results.csv')

#ADD INTERNAL_ID if desired

#%%
OLD VERSION OF TURNING HUME RESULTS BACK TO THE MATRIX
for i in range(len(full_date_api)):
    job = client.get_job(full_date_api[i].split(sep='"')[1])
    print("Job:", i," Results: ",job.get_status())
    job.download_artifacts("SectionstoRun/wwp"+str(i)+".zip")

    zip_file_path = f'SectionstoRun/wwp{i}.zip'
    # Specify the path to the CSV file within the zip folder
    csv_file_path_within_zip = f'url-0-output_file_{i+179}.txt/csv/output_file_{i+179}.txt/language.csv' 

    # Extract the CSV file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extract(member=csv_file_path_within_zip)

    hume_results = pd.read_csv(csv_file_path_within_zip)
    current_group = 0

    # Create a new column 'Entry' to identify groups based on 'Word' column
    hume_results['Entry'] = 0

    # When ENDENTRY appears, make the next words a different group
    for index, row in hume_results.iterrows():
        if row['Text'] == 'ENDENTRY':
            current_group += 1
        hume_results.at[index, 'Entry'] = current_group

    #Remove dummy early rows
    start_index = hume_results[hume_results['Text'].str.contains('rawLines',na=False)].index[0]
    hume_results = hume_results.loc[(start_index+1):]
    
    # Filter out rows with 'ENDENTRY in 'Word' column
    grouping = hume_results[hume_results['Text'] != 'ENDENTRY']

    # Group by 'Entry' and calculate the average score for each group
    columns = grouping.columns[8:61]
    result = grouping.groupby('Entry')[columns].mean().reset_index().query('Entry<200') #Remove leftover pieces

    # The last entry only posts up to the last line, the others are all 200 long
    if i ==len(full_date_api)-1:
        date_piece = needs_results.iloc[i*200:len(needs_results)]
    else:
        date_piece = needs_results.iloc[i*200:(i+1)*200].reset_index()
    all_hume = pd.concat([all_hume,pd.concat([date_piece,result],axis='columns')],axis='index')

#all_hume.to_csv('Results for each piece.csv')


#FROM GENERAL RESULTS, TO GROUPED BY DATE THEN BY ID
#To avoid averaging an average, calculate the total words scored
#%%
all_hume['Num words'] = all_hume['text'].str.count('\s') + 1
all_hume = all_hume[pd.notna(all_hume['UUID'])]
all_hume = all_hume[pd.notna(all_hume['index'])]
for col in range(7,60):
    for row in range(len(all_hume)):
        all_hume.iloc[row,col] = all_hume.iloc[row,col] * all_hume['Num words'].iloc[row]
dated = all_hume.drop(columns=['Unnamed: 0','UUID','text','index','Entry']).groupby('Date').sum(numeric_only=True).reset_index()
ided = all_hume.drop(columns=['Unnamed: 0','Date','text','index','Entry']).groupby('UUID').sum(numeric_only=True).reset_index()

#Gets new average for each emotion
for col in range(1,54):
    for row in range(len(dated)):
        dated.iloc[row,col] = dated.iloc[row,col] / dated['Num words'].iloc[row]
    
    for row in range(len(ided)):
        ided.iloc[row,col] = ided.iloc[row,col] / ided['Num words'].iloc[row]


pd.concat([pd.read_csv('already run by uuid.csv'),ided[ided.columns[0:54]]],axis='index').to_csv('new_uuid-hume.csv',index=False)
pd.concat([pd.read_csv('already run by date.csv'),dated[dated.columns[0:54]]],axis='index').to_csv('new_dates-hume.csv',index=False)

# %%


