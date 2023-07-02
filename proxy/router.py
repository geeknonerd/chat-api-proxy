from fastapi import APIRouter

from .config import get_settings
from .engine import G4fEngine
from .schema import Args

router = APIRouter()

engine = G4fEngine(get_settings().get_generator_cnf())


@router.api_route('/v1/chat/completions', methods=['GET', 'POST'])
async def chat_completions(args: Args):
    return engine.stream_response(args) if args.stream else engine.json_response(args)
