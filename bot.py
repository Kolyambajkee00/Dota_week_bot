import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from config import BOT_TOKEN
from opendota_client import (
    get_player_matches,
    get_player_info,
    extract_steam_id_from_text
)
from constants import get_hero_name, get_hero_image_name
from stats_calculator import calculate_stats
from records_db import init_db, update_records, format_records_message

init_db()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для анализа недельной статистики в Dota 2.\n\n"
        "Отправь мне Dota ID, Steam ID или ссылку на профиль.\n"
        "Команда /help для справки.\n\n"
        "Примеры:\n"
        "/stats 467410168\n"
        "/stats 76561198427675896\n"
        "/stats https://steamcommunity.com/profiles/76561198427675896"
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "/stats <DotaID, SteamID или ссылка> - статистика за неделю\n"
        "/records <SteamID> - личный рекорд KDA\n"
        "/help - справка\n\n"
        "Бот принимает:\n"
        "32-битный ID (467410168)\n"
        "64-битный ID (76561198427675896)\n"
        "Ссылку на профиль Steam"
    )


@dp.message(Command("records"))
async def cmd_records(message: types.Message):
    text = message.text.replace("/records", "").strip()

    if not text:
        await message.answer("Укажи Steam ID. Пример: /records 467410168")
        return

    player_id_32bit = extract_steam_id_from_text(text)

    if player_id_32bit is None:
        await message.answer("Не удалось распознать Steam ID.")
        return

    player_info = await get_player_info(player_id_32bit)

    if player_info is None:
        await message.answer(f"Игрок с ID {player_id_32bit} не найден.")
        return

    nickname = player_info['personaname']

    from records_db import get_records
    records = get_records(str(player_id_32bit))

    if records:
        await message.answer(
            f"Рекорд {nickname}\n\n"
            f"Лучший KDA за неделю: {records['best_kda']:.2f}\n"
            f"Установлен: {records['last_updated'][:10]}"
        )
    else:
        await message.answer(
            f"У игрока {nickname} пока нет сохранённых рекордов. Используй /stats."
        )


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    text = message.text.replace("/stats", "").strip()

    if not text:
        await message.answer("Укажи Steam ID или ссылку. Пример: /stats 467410168")
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    status_msg = await message.answer(f"Обрабатываю запрос...")

    player_id_32bit = extract_steam_id_from_text(text)

    if player_id_32bit is None:
        await status_msg.edit_text("Не удалось распознать Steam ID.")
        return

    player_info = await get_player_info(player_id_32bit)

    if player_info is None:
        await status_msg.edit_text(f"Игрок с ID {player_id_32bit} не найден.")
        return

    nickname = player_info['personaname']

    await status_msg.edit_text(f"Загружаю матчи для {nickname} (ID: {player_id_32bit}) за последние 7 дней...")

    matches = await get_player_matches(player_id_32bit, days=7)

    if matches is None:
        await status_msg.edit_text(f"Ошибка при загрузке данных от OpenDota. Попробуйте позже.")
        return

    if len(matches) == 0:
        await status_msg.edit_text(f"У игрока {nickname} нет матчей за последние 7 дней.")
        return

    stats = calculate_stats(matches)

    steam_id_str = str(player_id_32bit)
    update_records(steam_id_str, stats['avg_kda'])

    result = f"Статистика {nickname} за неделю\n\n"
    result += f"Всего игр: {stats['total_matches']} ({stats['wins']}-{stats['total_matches'] - stats['wins']})\n"
    result += f"Общий винрейт: {stats['winrate']}%\n\n"
    result += f"Radiant: {stats['radiant_winrate']}% ({stats['radiant_wins']}-{stats['radiant_games'] - stats['radiant_wins']})\n"
    result += f"Dire: {stats['dire_winrate']}% ({stats['dire_wins']}-{stats['dire_games'] - stats['dire_wins']})\n\n"
    result += f"Средний KDA: {stats['avg_kda']}\n\n"
    result += "Топ-5 героев:\n"

    for i, (hero_id, hero_stats) in enumerate(stats['sorted_heroes'], 1):
        hero_winrate = (hero_stats['wins'] / hero_stats['games']) * 100
        hero_name = get_hero_name(hero_id)
        result += f"{i}. {hero_name} — {hero_stats['games']} игр ({hero_winrate:.1f}%)\n"

    records_message = format_records_message(steam_id_str, stats['avg_kda'])
    result += f"\n{records_message}"

    await status_msg.edit_text(result)

    if stats['sorted_heroes']:
        album = MediaGroupBuilder()

        for i, (hero_id, hero_stats) in enumerate(stats['sorted_heroes'], 1):
            hero_winrate = (hero_stats['wins'] / hero_stats['games']) * 100
            hero_name = get_hero_name(hero_id)
            hero_image_name = get_hero_image_name(hero_id)
            caption = f"{i}. {hero_name}\n{hero_stats['games']} игр\n{hero_winrate:.1f}%"

            photo_path = f"heroes_photos/{hero_image_name}.png"

            if os.path.exists(photo_path):
                photo = FSInputFile(photo_path)
                album.add_photo(media=photo, caption=caption)

        if album._media:
            await message.answer_media_group(media=album.build())


async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())