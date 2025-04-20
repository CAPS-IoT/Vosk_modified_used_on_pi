# Speech Recognition Toolkit(MODIFIED)

Vosk is an offline open source speech recognition toolkit. We modified the toolkit to enable it to receive external features to
do speech recognition.

The class llmchat.py in vosk-api/python/example provides the entrance of recognition and also call the LLM to give response to the result.
The class server.py is the entrance of entire process which activates a Http server waiting for features from ESP32
 
The code on ESP32 side is in the main directory which captures the audio and convert to the MFCC features we need for recognition in Vosk.