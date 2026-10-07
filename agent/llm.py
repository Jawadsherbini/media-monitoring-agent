"""One shared Anthropic client, with a clear failure if the key is missing or still a placeholder."""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not _key or _key.startswith("your-"):
    raise RuntimeError(
        "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and paste your real key "
        "from console.anthropic.com, then run again.")
client = Anthropic(api_key=_key)
