##This script takes the directory containing wav files as input, convert each of the files into text 
##and save the corresponding text file in the output directory.
##python SpeechToText.py --input <input_dir_name> --output <output_dir_name>
import io
import os
import shutil
import sys
import argparse
import csv

# Imports the Google Cloud client library

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

OUTPUT_DIR = 'output'
INPUT_DIR = 'input'

parser = argparse.ArgumentParser()
parser.add_argument("--input","-i",help="input file directory")
parser.add_argument("--output","-o",help="output csv")

args = parser.parse_args()
if args.input:
    INPUT_DIR=args.input
if args.output:
    CSV_FILE=args.output

#delete older dir, create new directory to store generated text files
#shutil.rmtree(OUTPUT_DIR,ignore_errors=True)
#os.makedirs(OUTPUT_DIR)
##iterate over all the input wav files
file_counter=1
response_dict = {}
# Instantiates a client
client = speech.SpeechClient()
for wav_file in os.listdir(INPUT_DIR):
    print("**********************Generating text from audio files in folder :" + INPUT_DIR+" *****************************")
    if wav_file.endswith('.wav'):
        
        with io.open(INPUT_DIR+"/"+wav_file, 'rb') as audio_file:
            print("********* Now converting audio file : "+wav_file+" ************")
            # Loads the audio into memory
            content = audio_file.read()
            audio = types.RecognitionAudio(content=content)

        config =types.RecognitionConfig(encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
                                   # sample_rate_hertz=16000,
                                    language_code='en-US',
                                    ##enable_automatic_punctuation=True,
                                    max_alternatives=1)


        response = client.recognize(config, audio)

        #output_text = open(OUTPUT_DIR + '/generated_speech'+str(file_counter)+'.txt', 'w')
        file_counter+=1

        #with open(CSV_FILE,'a') as fd:
        for i in range(len(response.results)):
            for j in range(len(response.results[i].alternatives)):
                transcript = response.results[i].alternatives[j].transcript
                print('Transcript: {}'.format(transcript))
                if wav_file in response_dict:
                    response_dict[wav_file] = response_dict[wav_file] + transcript
                else:
                    response_dict[wav_file] = transcript
                #print("val in dict:",response_dict[wav_file])
                    #csv_writer = csv.writer(fd)
                    #csv_writer.writerow([wav_file,transcript])
                    #output_text.write('Alternative num. ' + str(j + 1)
                     #                 + ': ' + transcript + '\n')
columns = ['wav_file_name','response']

try:
    with open(CSV_FILE,'w') as csvfile:
        writer = csv.writer(csvfile)
        #writer.writeheader()
        for key,value in response_dict.items():
            #print("key:" +key, "val :" +value)
            writer.writerow([key,value])
except IOError:
    print('Error in writing csv')



 