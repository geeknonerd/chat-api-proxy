# import nest_asyncio

from proxy import create_app

# nest_asyncio.apply()
# start app
app = create_app()

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8000)
