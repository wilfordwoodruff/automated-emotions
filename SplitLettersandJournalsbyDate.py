#%%
import pandas as pd
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
import io
import sys
import numpy as np

    #FRESH API DOWNLOAD
def get_data(url, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        'Accept': 'application/json',
        'Content-Type': 'application/json' 
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return pd.read_csv(io.BytesIO(response.content))
    else:
        print(f"Error: {response.status_code} - {response.reason}")
        sys.exit(1)

def download_and_split_by_date():
    url = 'https://wilfordwoodruffpapers.org/api/v1/pages/export'

    all_api = get_data(url, os.getenv("WWP_KEY"))

    #START OF JOURNALS --------------------------------

    # Filter for "Journals" in the Document Type column
    all_journals = all_api[pd.notna(all_api['Original Transcript'])].query('`Document Type` == "Journals"')#[all_api['Document Type'] == "Journals"  len(all_api['Original Transcript']) >0]

    def process_row(row):
        #Collects all the date tagas, then splits the text on each appearance
        soup = BeautifulSoup(row['Original Transcript'], 'html.parser')
        date_tags = soup.find_all('time')
        dates = [tag.get('datetime') for tag in date_tags]
        split_pattern = r'<time datetime=".+?">'
        texts = re.split(split_pattern, row['Original Transcript'])

        #Saves time, if only one date is tied to the entry then grab it and move on
        if len(str(row.Dates))<=10:
            dates = [row.Dates for i in texts]

        #When the top part of a page is a continuation of previous day, that section won't have a date attached
        #This adds the previous day to the list
        elif len(texts) > len(dates):
            try:
                dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]
                dates.insert(0,dates[0]-timedelta(days=1))
                dates = [datetime.strftime(date, '%Y-%m-%d') for date in dates]
            except:
                dates.insert(0,None)

        return pd.DataFrame({
            'Parent_ID': row['Parent ID'],
            'order_id': row['Order'],
            'UUID': row['UUID'],
            'Internal ID': row['Internal ID'],
            'date': dates,
            'text': texts
        })

    # Build a new dataset that splits on the day tags and fills in gaps
    papers = pd.concat([process_row(row) for _, row in all_journals.iterrows()], ignore_index=True)

    # Convert date to datetime format and create a new date column in 'mm/dd/yyyy' format
    papers['date'] = pd.to_datetime(papers['date'], errors='coerce')
    papers['download_order'] = papers.index

    #Rows of these often get caught in the system (from the start of a page before the date)
    pattern = r'<p></p><p>(<strong>)?$'
    papers = papers[~papers['text'].str.contains(pattern, regex=True)]
    pattern = '<p></p><p><u>$'
    papers = papers[~papers['text'].str.contains(pattern, regex=True)]

    #Remove trailing tags, only a problem in journals
    for i in range(len(papers)):
        result = re.search(r'.*<br/>',papers['text'].iloc[i],re.DOTALL)
        if result:
            captured_text = result.group(0)
            papers['text'].iloc[i] = captured_text

    #FILLS IN MISSING VALUES ------------------------ 
    # 2 ways: by using the date from the previous row, or the previous Internal ID.
    #Previous row usually works, but Internal ID works better for edge cases (like if the document has only one entry)
    with_sort = pd.DataFrame()
    no_sort = pd.DataFrame()
    parent_ids = papers['Parent_ID'].unique()
    for parent_id in parent_ids:
        split = papers.query('Parent_ID == @parent_id')
        sort_split = split.sort_values(['order_id'])
        split['date'].ffill(inplace=True)
        sort_split['date'].ffill(inplace=True)
        no_sort = pd.concat([no_sort,split])
        with_sort = pd.concat([with_sort,sort_split])
    both_methods = (no_sort.set_index('download_order')
                    .join(with_sort.set_index('download_order'),lsuffix='_no_sort', rsuffix='_sort')
                    #.sort_values(['Parent_ID_sort','order_id_sort'])
    )

    #When two dates are similar, use the non-sorted method because the sorted method often moves around the days
    #within each document, so the last row isn't always the last day
    #When they're far apart, that means no-sort tried to fill from a previous document, so use the other method
    both_methods['days_between'] = (both_methods['date_sort'] - both_methods['date_no_sort'])
    both_methods['Date'] = np.where(abs(both_methods['days_between'].dt.days) < 10,both_methods['date_no_sort'],both_methods['date_sort'])
    both_methods['match_date'] = np.where(both_methods['Date'] == both_methods['date_no_sort'],False,True)
    #Overide days where there's no date archived
    both_methods['match_date'] = np.where(pd.isna(both_methods['date_sort']),True,both_methods['match_date'])
    both_methods['Date'] = np.where(pd.isna(both_methods['date_sort']),None,both_methods['Date'])

    both_methods['Date'] = [pd.Timestamp(date, unit='ns') for date in both_methods['Date']]

    changed_journals = both_methods.filter(['Parent_ID_no_sort','order_id_no_sort','UUID_no_sort','text_no_sort','Date'])
    changed_journals.columns = ['Parent_ID','order_id','UUID','text','Date']

    # START OF LETTERS -----------------------------------
    #Most entries have dates labeled in either First Date, Dates, or Parent Name values
    #This Compares the 3, and assigns the right value
    letters = all_api[all_api['Document Type']=='Letters']
    letters = letters[pd.notna(letters['Original Transcript'])]
    letters['First Date'] = letters['First Date'].fillna(' ')
    letters['Dates'] = letters['Dates'].fillna(' ')

    #Text format for most dates
    date_pattern = r'(\d{1,2})\s(\w+)\s(\d{4})'

    month_mapping = {'January': 1,'February': 2,'March': 3,'April': 4,'May': 5,'June': 6,'July': 7,'August': 8,'September': 9,'October': 10,'November': 11,'December': 12}

    letters_dated = pd.DataFrame(columns = ['Parent_ID','order_id','UUID','Internal ID','Date','text',],
                                index= range(len(letters['Internal ID']))
            )
    for i in range(len(letters['Internal ID'])):
        row = letters.iloc[i]
        #Get First Date, then Date, then parse the Parent Name
        if row['First Date']!=' ':
            find_date = row['First Date']
        elif row['Dates']!=' ':
            find_date = row['Dates']
        else:
            try:
                match = re.search(date_pattern, row['Parent Name'])
                if match:
                    #Probably inefficient, but it works
                    day, month_str, year = match.groups()
                    day = str(day)
                    month = str(month_mapping.get(month_str))
                    if len(day) == 1:
                        day = "0"+day
                    if len(month) == 1:
                        month = "0"+month
                    find_date = str(year)+'-'+str(month)+'-'+str(day)
                else:
                    find_date = 'error1' #Only happens if all 3 values have no date pattern
            except:
                find_date = 'error2' #Never happened in test cases, hopefully this doesn't happen
        letters_dated.iloc[i] = {'Parent_ID': row['Parent ID'],
            'order_id': row['Order'],
            'UUID': row['UUID'],
            'text': row['Original Transcript'],
            'Date': find_date
            }

    # START OF COMBINING JOURNALS & LETTERS, PLUS FIXING HTML TAGS ------------
    by_date = pd.concat([letters_dated, changed_journals], ignore_index=True)

    for i in range(len(by_date)):
        #Letters have tags at the end to remove
        #Tags need to be filled in this order: <p><strong><time>, so it starts from the inside out
        p_tags = by_date['text'].iloc[i].count('<p>')
        p_tags2 = by_date['text'].iloc[i].count('</p>')
        strong_tag = by_date['text'].iloc[i].count('<strong>')
        strong_tag2 = by_date['text'].iloc[i].count('</strong>')
        time_tag = by_date['text'].iloc[i].count('<time')
        time_tag2 = by_date['text'].iloc[i].count('</time>')
        if time_tag < time_tag2:
            by_date['text'].iloc[i] = ("<time>"*(time_tag2-time_tag)) + by_date['text'].iloc[i] 
        if strong_tag > strong_tag2:
            by_date['text'].iloc[i] = by_date['text'].iloc[i] + ("</strong>"*(strong_tag-strong_tag2))
        elif strong_tag < strong_tag2:
            by_date['text'].iloc[i] = ("<strong>"*(strong_tag2-strong_tag)) + by_date['text'].iloc[i] 
        if p_tags > p_tags2:
            by_date['text'].iloc[i] = by_date['text'].iloc[i] + ("</p>"*(p_tags-p_tags2))
        elif p_tags < p_tags2:
            by_date['text'].iloc[i] = ("<p>"*(p_tags2-p_tags)) + by_date['text'].iloc[i] 

    #Finally, there are a couple consistent errors to fix
    by_date['Date'] = by_date['Date'].replace({'error1':np.nan,"2/23/1934":'1897-08-14'})
    return(by_date[['UUID','Date','text']])

