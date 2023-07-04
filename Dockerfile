FROM python:3.9-slim-buster

WORKDIR /code
COPY requirements.txt /code
COPY gpt4free/requirements.txt /code/requirements-g4f.txt

RUN python3 -m pip install -i https://pypi.doubanio.com/simple/ --user --no-cache-dir --upgrade -r /code/requirements-g4f.txt
RUN python3 -m pip install -i https://pypi.doubanio.com/simple/ --user --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./gpt4free/g4f /code/g4f
COPY ./proxy /code/proxy
COPY ./ext /code/ext
COPY main.py /code

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
