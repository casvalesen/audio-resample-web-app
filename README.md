# Audio Resample Web App
An audio resampling web app in python using fastapi, ray and librosa. 

The app is designed for future flexibility. It is set up using the config.yml, which specifies output file type and sample rate, and a reference to the file_type_extensions.json which maps .This allows the app to be extended to future use cases as well as file types without one to one mapping between file type and extension (e.g AIFF -> (.aif, aifc)). 

The app receives a list of audio files as Uploadfile through FastAPI, verifies file format and resamples these in parallel with librosa using Ray workers. The app returns a zipped folder containing the resampled audio files. The test script sends in test audio files in both mp3 and wav format, receives and validates the API call response. 

Depending on specific deployment platform and compute (serverless, container etc.), the app can we further extended to autoscale with new requests. 

## Test files
The app includes some audio format testfiles in the 'test/test_files' folder for ease. 
- Test files are both in .mp3 and .wav formats
- Sample rates in 44.1kHz, 48kHz, and 16kHz to test both down and upsampling. 
- The smallest file is 7kb and largest 130,8mb. 

# Usage

## Docker deployment

'docker build -t resample-app:v1 .' to build

'docker run -it -d --name audio-resample-app -p 5000:5000 resample-app:v1' to run 

## Resample app conda deployment 

'conda env create -f app_env.yml' to create environment 

'python app/app.py' to launch application

## Test app 

'conda env create -f test_env.yml' to create environment 

'python test_script.py' to run test app. 

## testing with Pytest

'pytest test_script.py' runs two tests
- checking if there are files in the test file directory
- checking if we received the right number of .mp3 files

