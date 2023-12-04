import pandas as pd
import os
import zipfile
from hume import HumeBatchClient
hume_api_key = os.getenv('HUME_WWP_API')
client = HumeBatchClient(hume_api_key)
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

full_date_api = pd.read_csv('All_Hume_Results.csv')

def job_to_results(row):
    client.get_job(row['Job ID']).download_artifacts(f"SectionstoRun/wwp{row['Job ID']}.zip")
    zip_file_path = f'SectionstoRun/wwp{row["Job ID"]}.zip'
    # Specify the path to the CSV file within the zip folder
    csv_file_path_within_zip = f'text-0-file/csv/1/language.csv' 
    # Extract the CSV file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extract(member=csv_file_path_within_zip)

    results = pd.read_csv(csv_file_path_within_zip)[emotions].values[0].tolist()
    #Remove file so we aren't cluttered by thousands of documents
    #os.remove(zip_file_path)
    #os.remove(f'SectionstoRun/wwp{row["Job ID"]}/text-0-file/csv/1/language.csv')
    return results

#Gets the new, still-empty rows, grabs the Hume values, then updates the original
new_results = full_date_api[pd.isna(full_date_api['Admiration'])]
try: 
    new_results[emotions] = new_results.apply(job_to_results, axis=1, result_type='expand')
    full_date_api.update(new_results)
    full_date_api.to_csv('All_Hume_Results.csv',index=False)
except:
    print('Error collecting zip files. Hume.ai is probably still running, so try again in a few minutes.')