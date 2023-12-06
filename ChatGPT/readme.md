Emotion Analysis with GPT-3.5-turbo
-------------------------------------------------------------------------------
This Python script utilizes the OpenAI GPT-3.5-turbo model to analyze emotions in text data. The code reads a CSV file containing text entries, generates emotions analysis using the OpenAI API, and appends the results to an output CSV file.


Prerequisites
-------------------------------------------------------------------------------
Before running the script, ensure that you have the required Python packages installed. You can install them by executing the following command in Windows PowerShell (or whatever shell you are using):

pip install -r requirements.txt


Configuration
-------------------------------------------------------------------------------
Create a config.txt file with the following format:

api_key=<YOUR_OPENAI_API_KEY>

input_file_path=<PATH_TO_INPUT_CSV_FILE>

column_to_read=<COLUMN_NAME_TO_ANALYZE>

uid_column=<COLUMN_NAME_FOR_UUID>

Replace placeholders with your OpenAI API key and file paths.

Optionally, modify the requirements.txt file if additional Python packages are needed.


Usage
-------------------------------------------------------------------------------
Run the script using the following command in Windows PowerShell (or whatever shell you are using):

python emotion_analysis.py

The script will process the data, analyze emotions, and append the results to the specified output CSV file.


Output
-------------------------------------------------------------------------------
The script will create or update an output CSV file containing the UUIDs and corresponding emotion analysis results.


Note
-------------------------------------------------------------------------------
The script assumes that the input CSV file contains a column with UUIDs (uid_column) and a column with text entries (column_to_read).
The OpenAI API key is crucial for accessing the GPT-3.5-turbo model. Ensure that you keep it confidential and DO NOT publish it publicly to github.
Feel free to reach out for any questions or issues to the BYU-I Data Science Student Consulting Team! 
