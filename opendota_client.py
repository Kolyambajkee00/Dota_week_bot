import aiohttp
import re

OPENDOTA_API_URL = "https://api.opendota.com/api"

STEAM_64_OFFSET = 76561197960265728


def convert_to_32bit(steam_id: int) -> int:
    if steam_id < 2 ** 32:
        return steam_id
    else:
        return steam_id - STEAM_64_OFFSET


def extract_steam_id_from_text(text: str) -> int | None:
    numbers = re.findall(r'\d+', text)

    for num_str in numbers:
        num = int(num_str)
        if num < 10000:
            continue

        if num > STEAM_64_OFFSET:
            return convert_to_32bit(num)

        if num < 2 ** 32:
            return num

    return None


async def get_player_matches(steam_id_32bit: int, days: int = 7):
    url = f"{OPENDOTA_API_URL}/players/{steam_id_32bit}/matches"
    params = {'date': days}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Ошибка API: {response.status}")
                return None


async def get_player_info(steam_id_32bit: int):
    url = f"{OPENDOTA_API_URL}/players/{steam_id_32bit}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'personaname': data.get('profile', {}).get('personaname', 'Unknown'),
                    'rank_tier': data.get('rank_tier', 0),
                    'mmr_estimate': data.get('mmr_estimate', {}).get('estimate', 0)
                }
            else:
                return None