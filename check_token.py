import os
import json
import urllib.request
import urllib.error
from pathlib import Path

ENV_PATH = Path(__file__).parent / '.env'


def _get_token_from_env(path: Path) -> str | None:
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            if k.strip() == 'TELEGRAM_BOT_TOKEN':
                return v.strip()
    return None


def main():
    token = _get_token_from_env(ENV_PATH)
    if not token:
        print('No TELEGRAM_BOT_TOKEN found in .env')
        return

    url = f'https://api.telegram.org/bot{token}/getMe'
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode(errors='ignore')
        except Exception:
            body = '<no body>'
        print(f'HTTP error {e.code}: {body}')
        return
    except Exception as e:
        print('Network error or timeout:', e)
        return

    if not isinstance(data, dict):
        print('Unexpected response:', data)
        return

    if data.get('ok'):
        result = data.get('result', {})
        bot_id = result.get('id')
        username = result.get('username')
        is_bot = result.get('is_bot')
        print('Token is valid.')
        print('Bot ID:', bot_id)
        print('Bot username:', username)
        print('Is bot:', is_bot)
    else:
        print('Token is invalid or revoked. Response:')
        print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
