from fastapi import APIRouter

from .config import get_settings
from .engine import G4fEngine, ApiEngine
from .schema import Args

router = APIRouter()
settings = get_settings()

engine = ApiEngine(settings.get_generator_cnf()) if settings.mode == 'api' else G4fEngine(settings.get_generator_cnf())


@router.api_route('/v1/chat/completions', methods=['GET', 'POST'])
async def chat_completions(args: Args):
    return engine.stream_response(args) if args.stream else engine.json_response(args)
