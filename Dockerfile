#Pull base
FROM python:3.8 

#Set working directory
WORKDIR /usr/src/app

#Copy requirements file
COPY ./requirements.txt /usr/src/app/requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#install app depencendcies 
RUN pip install -r /usr/src/app/requirements.txt

RUN apt-get update && apt-get install -y libsndfile1

#Copy over necessary files 
COPY app/app.py /usr/src/app/app.py
COPY app/config.yml /usr/src/app/config.yml 
COPY app/file_type_extensions.json /usr/src/app/file_type_extensions.json

#initiate app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]