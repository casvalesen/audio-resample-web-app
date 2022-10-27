# Send request 
import os 
import requests
import tempfile 
import zipfile
import pytest

#Setup endpoint to test
app_host_port = "http://localhost:5000"
resample_endpoint = 'resample_parallel'
test_files_dir = 'test_files'
resampled_files_dir = 'resampled_files'

class AppTest: 
    def __init__(self, app_host_port, resample_endpoint,test_files_dir, resampled_files_dir):
        self.app_host_port = app_host_port
        self.resample_url =  f'{app_host_port}/{resample_endpoint}'
        self.test_files_dir = test_files_dir
        self.resampled_files_dir = resampled_files_dir

        return None 
        
    def send_receive_files(self):

        audio_test_files = ['long_a_place_to_rest.wav', 'medium_a_classic_education.wav','short_testcase_AudioMNIST_data_01_0_01_0.mp3']

        audio_test_file_name_1 = audio_test_files[0]
        print(audio_test_file_name_1)
        audio_test_file_path_1 =  os.path.join(self.test_files_dir, audio_test_file_name_1)

        audio_test_file_name_2 = audio_test_files[1]
        print(audio_test_file_name_2)
        audio_test_file_path_2 =  os.path.join(self.test_files_dir, audio_test_file_name_2)

        post_content_list = [("files",open(audio_test_file_path_1, 'rb')),("files", open(audio_test_file_path_2, 'rb'))]
    
        #Post request to server
        resample_response = requests.post(self.resample_url, files= post_content_list)

        resampled_filename = resample_response.headers['filename']
        resampled_file_path = f'{resampled_files_dir}/{resampled_filename}'

        #Handle received files
        temp_zip = tempfile.NamedTemporaryFile()
        temp_zip.write(resample_response.content)
        with zipfile.ZipFile(temp_zip.name, 'r') as archive:
            archive.extractall(path = resampled_files_dir)

        received_file_list = os.listdir(os.path.join(os.getcwd(),resampled_files_dir))

        return received_file_list, post_content_list

#Run call
def main(): 
    received_file_list, post_content_list = AppTest(app_host_port, resample_endpoint,test_files_dir).send_receive_files()

    print(f'Received files {received_file_list} back from resample app')


#Add tests
def test_files_exist(app_test = AppTest(app_host_port, resample_endpoint,test_files_dir, resampled_files_dir)):

    assert len(os.listdir(app_test.test_files_dir)) != 0 

    return None 

def test_responses(app_test = AppTest(app_host_port, resample_endpoint,test_files_dir, resampled_files_dir)):
    '''
    Tests we received as many files back as posted
    '''

    received_file_list, post_content_list = app_test.send_receive_files()

    received_mp3_files = [file for file in os.listdir(app_test.resampled_files_dir) if file.split('.')[-1] == 'mp3']

    #Check that we got back as many files as we expected
    assert len(received_mp3_files)==len(post_content_list)

    return None

if __name__=="__main__":
    main()
