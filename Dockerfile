FROM python:3.9-slim-buster

WORKDIR /code
COPY requirements.txt /code/requirements.txt
COPY gpt4free/requirements.txt /code/requirements-g4f.txt
COPY ./gpt4free/g4f /code/g4f

RUN python3 -m pip install -i https://pypi.doubanio.com/simple/ --no-cache-dir --upgrade -r /code/requirements-g4f.txt
RUN python3 -m pip install -i https://pypi.doubanio.com/simple/ --no-cache-dir --upgrade -r /code/requirements.txt
WORKDIR /code/g4f

WORKDIR /code
COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
