
from __future__ import division

import re
import sys

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import pyaudio
from six.moves import queue
import datetime
import wave

# Audio recording parameters
RATE = 16000
CHUNK = 100
audioFile = "recording.wav"
frames=[]
LANGUAGE_CODE = 'en-US'
FILE_NAME = 'generated_speech.txt'

class MicStreaming(object):
    ##Opens a recording stream as a generator yielding the audio chunks

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True
      

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        wf = wave.open(audioFile,'wb')
        wf.setnchannels(1)
        wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()


        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        ##Continuously collect data from the audio stream, into the buffer.
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            frames.append(chunk)
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                    frames.append(chunk)

                except queue.Empty:
                    break

            yield b''.join(data)


def fetch_responses(responses):

    file = open(FILE_NAME, "w")
    num_chars_printed = 0
    exitFlag = False;
    ## Iterating through server responses
    for response in responses:
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue

        for i in range(len(result.alternatives)):
            #print("num of alternatives",len(result.alternatives))
            transcript = result.alternatives[i].transcript
            overwrite_chars = ' ' * (num_chars_printed - len(transcript))
            if not result.is_final:
                sys.stdout.write(transcript + overwrite_chars + '\r')
                sys.stdout.flush()
                num_chars_printed = len(transcript)
            else:
                print(transcript + overwrite_chars)
                file.write("alternative no. "+str(i+1)+ ": "+transcript +"\n")

                # Exit recognition if any of the transcribed phrases contains exit
                if re.search(r'\b(exit|quit)\b', transcript, re.I):
                    exitFlag=True
                    print('Exiting..')
                    break
        if exitFlag:
            break
            num_chars_printed = 0


def main():

    client = speech.SpeechClient()
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=LANGUAGE_CODE,
        enable_automatic_punctuation=True,
        max_alternatives=3
)
    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=True)

    with MicStreaming(RATE, CHUNK) as stream:
        audio_generator = stream.generator()

        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)
        responses = client.streaming_recognize(streaming_config, requests)


        fetch_responses(responses)


if __name__ == '__main__':
    main()
