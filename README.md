# automated-emotions

This will take every unscored entry from the Wilford Woodruff Papers and give them an emotion value.
<br>
This has multiple steps.
1. Run `Step 1.py`, which collects the most recent API pull and separates new documents into 200-entry chunks
2. Push this folder back to Github. We'll use the new raw text in the `SectionstoRun` folder for Hume
3. Run `Step 2.py`, that will send each chunk to Hume and save the Job ID for later
4. Wait a few hours for Hume. Most of the entries will run right away and don't take long, but every so often, Hume will 'queue' a single entry and wait an hour or so to actually run the results.
5. Run `Step 3.py`, which collects all the results from Hume, matches them back to each text. It also re-configures an output by date, instead of UUID, which makes timeline tracking a little easier.
6. Now save the values from `new_uuid-hume.csv` into the system, and change it to `already run by id.csv` so that the next time it runs this'll save.
7. Delete the files in SectionstoRun so that old, high-numbered entries don't get rerun

<br>
Stuff to figure out for the future:
+ Remove the 179 from Step 3 when it runs on real documents
+ GPT needs to run automatically too. Which step should that be?
+ Remove the text in SectionstoRun after a round, so that old, high-numbered entries don't get rerun
+ Save the Job ID for each entry moving forward to make it easier to trace back values