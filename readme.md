## Emotion Recognition Engines for the WWPapers
We have two different algorithms prepared:
+ Hume.ai, a research program designed specifically for recognizing emotions
+ ChatGPT, a generalized text chatbot with customizable functionality

At the moment, the two functions work independently and are structured slightly differently

+ The Hume.ai folder will automatically pull from the API add get emotion scores for new documents
+ The GPT folder can take any document with missing GPT values and automatically get the new scores.
We should add direct compatability soon, but the best way to use both at the moment would be this:
1. Run `Part 1.py` in the Hume.ai folder.
2. Open `All_Hume_Results.csv` and grab the lines that don't have any emotion scores. These will be the new documents that need scores for both.
3. Copy those into `recent_wwp_documents.csv`, and in `config.txt` make uuid_column=text.
4. Run `gpt_emo.py` on that new document (The Hume.ai model needs time to run anyway).
5. Run `Part 2 after Hume.py` in the Hume.ai folder to get the final results for that.