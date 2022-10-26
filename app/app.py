import time 
import uvicorn
from typing import List
import ray
import yaml
import json 
import os
import tempfile
import zipfile
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.testclient import TestClient
from starlette.background import BackgroundTask
from pydantic import BaseModel 
import librosa
import soundfile as sf

#Set program configs
PATH_TO_CONFIG = 'config.yml'

try: 
    with open(PATH_TO_CONFIG, 'r') as file: 
        app_config = yaml.safe_load(file)
        print(f'Successfully loaded config from {PATH_TO_CONFIG}')
except: 
    raise IOError(f'Could not open config file {PATH_TO_CONFIG}, check it exists')

output_file_type = app_config['output_file_type']
output_sample_rate = app_config['output_sample_rate']

PATH_TO_FILE_TYPE_EXTENSION_MAP = app_config['file_type_extensions_map']

try: 
    with open(PATH_TO_FILE_TYPE_EXTENSION_MAP,'r') as file: 
        file_type_extension_map = json.loads(file.read())
        print(f'Loaded file type extension map from {PATH_TO_FILE_TYPE_EXTENSION_MAP}')
except: 
    raise IOError(f'Could not open file type extensions map at {PATH_TO_FILE_TYPE_EXTENSION_MAP}, check it exists')

output_file_extension = file_type_extension_map[output_file_type]
print(f'Using output file_extension {output_file_extension}')


class TestMessage(BaseModel):
    message: str
    wait: int

async def message_handler(message):
    starttime = time.strftime("%X")
    print(f'Got message {message.message} \n Wait time: {message.wait} \n started at {time.strftime("%X")}')
    await asyncio.sleep(message.wait)
    print(f'Returning {message.message} \n Finished at {time.strftime("%X")}')
    endtime = time.strftime("%X")
    
    return {'message': message.message, 'startime': starttime , 'endtime': endtime }

#Define paralell handling of files

#Start ray
ray.init(ignore_reinit_error=True)


@ray.remote
def resample_files(file_path, file):
    '''
    Resampling function. 

    file_path: str, 
    file: 

    returns: dict, with filename, starttime, endtime and resampled test file
    
    '''

    #Log starttime of process
    starttime = time.strftime("%X")

    #Handle filename
    file_name_elements = file_path.split('.')
    file_extension = file_name_elements[-1]
    file_name = file_name_elements[0]

    #Raise exception if wrong file type is passed 
    if file_extension not in file_type_extension_map.values():
        raise HTTPException(status_code = 401, detail = f'Received file does not have a valid file extension, current implemented extensions are {file_type_extension_map.values()}')
    else: 
        print(f'Initiatiing resample for {file_name},  \n filetype {type(file)} ')

    #Save file as temp for referenceable
    temp_received_file = tempfile.NamedTemporaryFile(suffix = f'.{file_extension}')
    temp_received_file.write(file)
    
    print(f'name of temp received file: {temp_received_file.name}, \n type: {type(temp_received_file)}')

    #Invoke resample service 
    orig_sr = librosa.get_samplerate(temp_received_file.name)  #file_path
    received_file, _ = librosa.load(temp_received_file.name, sr = orig_sr) #file_path
    resampled_testfile = librosa.resample(received_file, orig_sr=orig_sr, target_sr=output_sample_rate)

    endtime = time.strftime("%X")
    
    return {"filename": file_name, "starttime":starttime, "endtime": endtime, "resampled_file": resampled_testfile } 

#Define app 
app = FastAPI()

## Test functions
@app.post("/testmessage")
async def message(message: TestMessage):
    result = await message_handler(message)
    return result

@app.post("/resample_parallel")
async def resample_parallel(files: List[UploadFile]=File(...), response_model = List[FileResponse]):

    resampled_result_ids = []

    #Starts reveral ray processes
    for file in files:
         #Get audio file 
        file_path = file.filename
        file_name_elements = file_path.split('.')
        file_extension = file_name_elements[-1]
        file_name = file_name_elements[0] 
        print(f'Got file {file_name}, passing to ray')

        #Raise exception if wrong file type is passed 
        if file_extension not in file_type_extension_map.values():
            raise HTTPException(status_code = 401, detail = f'Received file does not have a valid file extension, current implemented extensions are {file_type_extension_map.values()}')

        resampled_result_ids.append(resample_files.remote(file_path=file.filename , file=file.file.read()))

    #Get results from ray workers
    resampled_results = ray.get(resampled_result_ids)

    #Sanity check resampled file returned from ray worker
    print(f'Type of resampled_file: {type(resampled_results[0]["resampled_file"])}')

    file_list = []
    zip_file_path = 'zip_resampled_files.zip'
    with zipfile.ZipFile(zip_file_path, mode = 'w') as archive: 
        for resampled_result in resampled_results:
                resampled_file_path = f'resampled_{resampled_result["filename"]}.{output_file_extension}'
                sf.write(resampled_file_path, resampled_result["resampled_file"], samplerate = output_sample_rate, format = output_file_type)
                file_list.append(resampled_file_path) 
                archive.write(resampled_file_path)
    
    def cleanup():
        os.remove(zip_file_path)
        for file_name in file_list:
            os.remove(file_name)

    return FileResponse(zip_file_path, headers = {'filename':zip_file_path}, background = BackgroundTask(cleanup))

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5000)
