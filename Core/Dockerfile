FROM python:3.10

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y

COPY . .

EXPOSE 7700
EXPOSE 7701

CMD ["python3","-u","app.py"]
