#Running Hume.ai on the Wilford Woodruff Papers
Welcome! This folder lets you collect new entries, assign them to Hume.ai jobs, then get the results. The results end up in `All_Hume_Results.csv`, which automically updates every time you follow the steps below:

### Note
On line 27 of `Part 1.py`, it currently reads:
`full_date_api = full_date_api[pd.notna(full_date_api['FixedText'])].head(n=50)`
<br>

Since we've hardly run these texts with the new Hume.ai results, at the moment during testing it'll only run the first 50 entries (some of which already have results and get skipped). Feel free to adjust this value as you're testing, the final product will remove this.


1. Run `Part 1.py`, which will:
+ Collect the documents API pull from the papers website
+ Run `SplitLettersandJournalsbyDate.py`, dividing the papers into the smallest unit of writing: a single day's values on a single page. (At the moment, these don't have a consistent unique ID, because it has to rearrange entries to confirm the dates)
+ Assigns each entry a unique Job ID to Hume.ai, for Hume to start getting emotion scores.
+ Saves all of those scores to `All_Hume_Results.csv`, which keeps every text sent in so far, it's Job ID, and (if that line was run previously) the 53 emotion scores.
2. Wait a couple hours for Hume.ai to complete all the jobs.
+ Most entries run fairly quick, but every so often one will "queue" in the system and stall out, which can take up to an hour.
3. Run `Part 2 after Hume.py`, which will collect all the Hume.ai results for entries without any emotion values and save them to the proper entry.
<br>
Every document entry gets a single value for 53 different emotions. At the moment, the best way to do that is through the HumeBatchClient aspect of Hume, running on 'conversational_turn' through their text feature. 

### Things to work out
+ Remove the zip files from `SectionstoRun` when we're done
+ Confirm that using FixedText as an index won't break anything
