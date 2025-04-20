# Speech Recognition Toolkit(MODIFIED)

Vosk is an offline open source speech recognition toolkit. We modified the toolkit to enable it to receive external features to
do speech recognition.

## Dependencies
python3.9.21
Vosk
Kaldi-tookit


## Getting Started


### Overview
The class llmchat.py in vosk-api/python/example provides the entrance of recognition and also call the LLM to give response to the result.
The class server.py is the entrance of entire process which activates a Http server waiting for features from ESP32
 
outt.txt is the file that stores features
In our configurations, we need also a 10s 16-bit 16000Hz PCM audio file(rec5.wav) as a dummy audio file.

### Build
```bash
python3 server.py
```
