from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware


async def auth_by_token(request: Request):
    """Auth by token, if token is None, then skip"""
    from .config import get_settings

    token = request.headers.get('token', '')
    auth_token = get_settings().auth_token
    if not auth_token:
        return
    if token.lstrip('Bearer ') == auth_token:
        return
    raise HTTPException(status_code=403)


def create_app() -> FastAPI:
    """initialize app"""
    from .router import router
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins="*",
        allow_headers=['*'],
        allow_methods=['OPTIONS', 'GET', 'POST', 'DELETE', 'PUT'],
        max_age=3600
    )
    app.include_router(router, dependencies=[Depends(auth_by_token)])
    return app
