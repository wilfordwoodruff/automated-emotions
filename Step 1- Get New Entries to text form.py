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

full_date_api = download_and_split_by_date()
#%%
already_run_id = pd.read_csv("already run by uuid.csv")
already_run_date = pd.read_csv('already run by date.csv')
needs_results = full_date_api.query("UUID not in @already_run_id['UUID']")
needs_results.head()

# Formats text
needs_results['FixedText'] = (needs_results['text'].str.replace("<.*?>",repl='',regex=True)
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
needs_results = needs_results[pd.notna(needs_results['FixedText'])]
# SPLIT EVERY 200 ENTRIES into their own text file
rows_in_set = 0
text = ''
num_documents = 0
for row in range(len(needs_results)):
    text = text + needs_results['FixedText'].iloc[row] + " ENDENTRY "
    rows_in_set += 1
    if rows_in_set==200 or row == len(needs_results)-1:
        output_filename = f'SectionstoRun/output_file_{num_documents}.txt'
        with open(output_filename, 'w', encoding='utf-8') as file:
            file.writelines(text)
        num_documents += 1
        text = ''
        rows_in_set=0

needs_results.to_csv('New Entries to Match with Hume.csv')
# %%
