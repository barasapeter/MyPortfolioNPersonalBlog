- create a virtual environment
```
python3 -m venv venv
```
- activate it
```
source venv/bin/activate (Linux)
.\venv\Scripts\Activate.ps1 (Windows)
```
- install required requirements (one-by-one) or use requirements.txt

- run the uvicorn server
```
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

- if installed requirements.txt manually, please save them on the requirements.txt file
```
pip freeze > requirements.txt (Windows)
pip3 freeze > requirements.txt (Linux)
```

- Create a Dockerfile. A.K.A the "Recipe". Is this the image?
```
FROM python:3.13.2-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt


```

- to avoid copying unnecessary files to the container, add .dockerignore file

- next, create a docker-compose.yaml file
```
services:
    web:
        build: .
        command: sh -c "uvicorn main:app --reload --port=8000 --host=0.0.0.0"
        ports:
            - 8000:8000
```

- build the container
```
docker compose up --build
```

- stop the container
```
CTRL + C
```

- rerun the container
```
docker compose up
```