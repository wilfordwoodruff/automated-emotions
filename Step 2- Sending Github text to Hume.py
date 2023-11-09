import pandas as pd
import os
import time
from hume import HumeBatchClient
from hume.models.config import LanguageConfig

# AFTER PUSHING TO GITHUB
hume_api_key = os.getenv('HUME_WWP_API')
pd.DataFrame().to_csv('Current_Hume_IDs.csv')
client = HumeBatchClient(hume_api_key)

def HumePerPage(page_num,hume_jobs):
    url = ''
    config = LanguageConfig(sentiment={})
    job = client.submit_job([url], [config])
    hume_jobs.append(str(page_num)+str(job))
    pd.Series(hume_jobs).to_csv('Hume_IDs.csv')

    print("Job",page_num," saved. Waiting for next", job)
    time.sleep(20)
    return hume_jobs
hume_jobs = pd.read_csv('Current_Hume_IDs.csv')['0'].tolist()
for i in range(len(hume_jobs)):
    hume_jobs=HumePerPage(i, hume_jobs)