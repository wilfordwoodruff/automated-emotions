import pandas as pd
from hume import HumeBatchClient
import zipfile
import os
#Sometimes it queues pages without explanation, so run this a couple hours later just in case
all_hume = pd.DataFrame()
hume_api_key = os.getenv('HUME_WWP_API')
client = HumeBatchClient(hume_api_key)
needs_results = pd.read_csv('New Entries to Match with Hume.csv')
hume_jobs = pd.read_csv('Hume_IDs.csv')['0'].tolist()

for i in range(len(hume_jobs)):
    job = client.get_job(hume_jobs[i].split(sep='"')[1])
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

    
    if i ==len(hume_jobs)-1:
        date_piece = needs_results.iloc[i*200:len(needs_results)]
    else:
        date_piece = needs_results.iloc[i*200:(i+1)*200].reset_index()
    all_hume = pd.concat([all_hume,pd.concat([date_piece,result],axis='columns')],axis='index')

all_hume.to_csv('Results for each piece.csv')

#%%
#FROM GENERAL RESULTS, TO GROUPED BY DATE THEN BY ID
#To avoid averaging an average, calculate the total words scored
all_hume = pd.read_csv('Results for each piece.csv')#all_hume
all_hume['Num words'] = all_hume['text'].str.count('\s').replace({0:1})
all_hume = all_hume[pd.notna(all_hume['UUID'])]
all_hume = all_hume[pd.notna(all_hume['index'])]
for col in range(7,61):
    for row in range(len(all_hume)):
        all_hume.iloc[row,col] = all_hume.iloc[row,col] * all_hume['Num words'].iloc[row]
#%%
dated = all_hume.drop(columns=['Unnamed: 0','UUID','text','index','Entry']).groupby('Date').sum(numeric_only=True).reset_index()
ided = all_hume.drop(columns=['Unnamed: 0','Date','text','index','Entry']).groupby('UUID').sum(numeric_only=True).reset_index()

#Gets new average for each emotion
for col in range(1,53):
    for row in range(len(dated)):
        dated.iloc[row,col] = dated.iloc[row,col] / dated['Num words'].iloc[row]
    
    for row in range(len(ided)):
        ided.iloc[row,col] = ided.iloc[row,col] / ided['Num words'].iloc[row]


pd.concat([pd.read_csv('already run by id.csv'),ided[ided.columns[0:54]]],axis='index').to_csv('new_uuid-hume.csv',index=False)
pd.concat([pd.read_csv('already run by date.csv'),dated[dated.columns[0:54]]],axis='index').to_csv('new_dates-hume.csv',index=False)
# %%
