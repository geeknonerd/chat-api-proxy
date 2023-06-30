# Chat API Proxy


![GitHub issues](https://img.shields.io/github/issues/geeknonerd/chat-api-proxy)
![GitHub forks](https://img.shields.io/github/forks/geeknonerd/chat-api-proxy)
![GitHub stars](https://img.shields.io/github/stars/geeknonerd/chat-api-proxy)


Chat API Proxy是一个免费的接口服务，基于OpenAI的接口格式开发，用于无缝替代OpenAI接口。
该服务使用了OpenAI GPT-4为基础的[GPT4Free](https://github.com/xtekky/gpt4free)项目。


## To-Do 清单 ✔️

- [x] 集成 GPT4Free
- [x] Docker 支持
- [ ] 支持配置文件适配其他免费接口
- [ ] 支持共享插件的方式使用大家提供的免费接口
- [ ] 支持免费接口池搭建稳定服务


## 功能

* 无缝替代OpenAI接口
* 支持与OpenAI接口一样的请求和响应格式
* 免费使用，无需支付额外费用


## 使用方法

### 1. 安装Python

请确保你的环境已安装下列软件：
- Python 3.8+


### 2. 克隆仓库并安装依赖

```shell
git clone https://github.com/geeknonerd/chat-api-proxy.git
cd chat-api-proxy

git submodule init
git submodule update

ln -s $(pwd)/gpt4free/g4f $(pwd)

python3 -m pip install -r gpt4free/requirements.txt
python3 -m pip install -r requirements.txt
```

### 3. 运行服务
```shell
python3 -m uvicorn app.main:app --reload
```
然后你就可以在 http://localhost:8000/ 访问到你的 API 服务了。

### 4. 调用API
我们的 API 接口的使用方法与 OpenAI 的完全相同。
例如，下面是一个使用 Python Openai SDK 发送请求的例子：

```python
import openai

openai.api_key = ""
openai.api_base = "http://localhost:8000/v1"

# create a chat completion
chat_completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello world"}])
# print the chat completion
print(chat_completion.choices[0].message.content)
```

下面是 python requests 发送请求的例子：
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    json={
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello world"}]
    })
print(response.json()['choices'][0]['message']['content'])
```

下面是使用 curl 发送请求的例子：
```shell
curl http://localhost:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "user", "content": "Hello world"}
  ]
}'
```


## Docker 🐳

### 预安装
在开始之前，请确保你已经在你的机器上安装了[Docker](https://www.docker.com/get-started)。

### 运行 Docker

使用 Docker 运行应用程序：
```
docker run -d --name chatproxy -p 8000:8000 geeknonerd/chat-api-proxy
```

通过以下 URL 在浏览器中访问应用程序：
```
http://127.0.0.1:8000
```
或者
```
http://localhost:8000
```

当你使用完应用程序后，使用以下命令停止 Docker 容器：
```
docker stop chatproxy
```


## 贡献
我们非常欢迎所有人的贡献，如果你在使用过程中发现任何问题或有好的建议，
都可以通过提交 Issue 或者 Pull Request 的方式告诉我们。


## 免责声明
本项目完全开源免费，仅供研究和学习使用，任何因使用该服务而导致的直接或间接的损失，我们概不负责。

