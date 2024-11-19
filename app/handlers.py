import re
import requests
import app.database as rq

from app.keyboards import get_callback_btns

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputMedia
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from dotenv import load_dotenv

from app.filters import IsAdmin
from app.middlewares import AlbumMiddleware
from app.utils import replace_prices_with_uah

load_dotenv()

router = Router()
# router.message.filter(IsAdmin())
router.message.middleware(AlbumMiddleware())


# admin /admin
@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Введіть повідомлення, яке потрібно конвертувати 👇")


main_btns = {"Редагувати": "edit", "Надіслати в групи": "send_to_groups"}


class ChannelIdState(StatesGroup):
    add_channel_id = State()
    remove_channel_id = State()


@router.message(
    Command("add_channel")
)  # Фільтр, що реагує тільки на повідомлення з каналу
async def save_channel_id(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Введіть ID")
    await state.set_state(ChannelIdState.add_channel_id)


@router.message(ChannelIdState.add_channel_id)
async def save_channel_id(message: Message, state: FSMContext):
    channel_id = message.text
    result = await rq.orm_add_channel(channel_id)

    if result:
        await message.answer("Канал успішно додано")
    else:
        await message.answer("Канал вже існує")

    await state.clear()


@router.message(Command("remove_channel"))
async def remove_channel_id(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Введіть ID")
    await state.set_state(ChannelIdState.remove_channel_id)


@router.message(ChannelIdState.remove_channel_id)
async def remove_channel_id(message: Message, state: FSMContext):
    channel_id = message.text
    result = await rq.orm_remove_channel(channel_id)

    if result:
        await message.answer("Канал успішно видалено")
    else:
        await message.answer("Канал не знайдено")

    await state.clear()


@router.message(Command("list"))
async def list_channels(message: Message, state: FSMContext):
    await state.clear()
    
    channels = await rq.orm_get_channels()
    channels_str = ''
    
    for channel in channels:
        channels_str += f'{channel.channel_id}\n'
        
    await message.answer(channels_str)


@router.message(StateFilter(None))
async def convert(message: Message, state: FSMContext, album: list[Message]):
    if not (
        (message.photo and message.caption) or  # Окреме фото з підписом
        (album and any(msg.caption for msg in album))  # Альбом з хоча б одним підписом
    ):
        await message.answer("Приймаються тільки картинки або альбоми з підписом.")
        return
    
    await state.clear()

    text = message.caption
    response = requests.get(
        "https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=11"
    )

    if not response.ok:
        await message.answer("Помилка під час отримання курсу валют")
        return

    data = response.json()
    exchange_rate = float(data[1]["buy"])
    updated_text = replace_prices_with_uah(text, exchange_rate)
    
    media_group = []
    for msg in album:
        if msg.photo:
            file_id = msg.photo[-1].file_id
            media_group.append(InputMediaPhoto(media=file_id))
    
    
    await message.answer_media_group(media=media_group)
    await message.answer(updated_text, reply_markup=get_callback_btns(btns=main_btns))
    await state.update_data(media_group=media_group, lines=updated_text.split("\n"))

@router.callback_query(F.data == "send_to_groups")
async def send_to_groups(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lines = data.get("lines", [])
    media_group = data.get("media_group", [])

    if not media_group:
        await callback.message.answer("Альбом не знайдено у стані.")
        return

    channels = await rq.orm_get_channels()

    for channel in channels:
        if re.match(r'^[0-9-]+$', channel.channel_id):
            try:
                media_group_with_caption = [
                    InputMediaPhoto(media=item.media, caption="\n".join(lines)) if idx == 0 else item
                    for idx, item in enumerate(media_group)
                ]
                await bot.send_media_group(chat_id=int(channel.channel_id), media=media_group_with_caption)
            except Exception as e:
                await callback.message.answer(f"Помилка надсилання до каналу {channel.channel_id}")
        else:
            await callback.message.answer(f"Канал {channel.channel_id} не знайдено")

    await callback.message.edit_text("Повідомлення надіслані")

@router.callback_query(F.data == "back")
async def back(callback: CallbackQuery, state: FSMContext):
    lines = await state.get_value("lines")
    await callback.message.edit_text("\n".join(lines), reply_markup=get_callback_btns(btns=main_btns))

@router.callback_query(F.data == "edit")
async def edit(callback: CallbackQuery, state: FSMContext):
    lines = await state.get_value("lines")
    numbered_lines = [f"{i + 1}. {line}" for i, line in enumerate(lines)]
    new_text = "\n".join(numbered_lines)

    btns = {
        "Добавити перехід на новий рядок": "add_line",
        # "Видалити перехід на новий рядок": "remove_line",
        "Виділити жирним": "add_bold",
        "Назад": "back",
    }

    await state.update_data(lines=[f"{line}" for line in lines])
    await callback.message.edit_text(
        new_text, reply_markup=get_callback_btns(btns=btns, sizes=(1,))
    )


@router.callback_query(F.data == "add_line")
async def add_line(callback: CallbackQuery, state: FSMContext):
    lines = await state.get_value("lines")
    numbered_lines = [f"{line}" for i, line in enumerate(lines)]
    btns = {}

    for count, line in enumerate(numbered_lines):
        btns[line] = f"line_{count+1}"
    
    btns["Назад"] = "back"

    await callback.message.edit_text(
        "Виберіть рядок 👇", reply_markup=get_callback_btns(btns=btns, sizes=(1,))
    )


@router.callback_query(F.data.startswith("line_"))
async def add_line(callback: CallbackQuery, state: FSMContext):
    line_number = int(callback.data.split("_")[1])
    lines = await state.get_value("lines")
    lines.insert(line_number, "")
    new_text = "\n".join(lines)

    await callback.message.edit_text(
        new_text, reply_markup=get_callback_btns(btns=main_btns)
    )
    await state.update_data(lines=lines)


# @router.callback_query(F.data == "remove_line")
# async def remove_line(callback: CallbackQuery, state: FSMContext):
#     lines = await state.get_value("lines")
#     numbered_lines = [f"{line}" for i, line in enumerate(lines)]
#     btns = {}

#     for count, line in enumerate(numbered_lines):
#         btns[line] = f"remove_line_{count+1}"

#     await callback.message.edit_text(
#         "Виберіть рядок для видалення 👇",
#         reply_markup=get_callback_btns(btns=btns, sizes=(1,)),
#     )


# @router.callback_query(F.data.startswith("remove_line_"))
# async def remove_line(callback: CallbackQuery, state: FSMContext):
#     line_number = int(callback.data.split("_")[2]) - 1  # Отримуємо індекс для видалення
#     lines = await state.get_value("lines")

#     if 0 <= line_number < len(lines):  # Перевірка, чи рядок існує
#         lines.pop(line_number)

#     new_text = "\n".join(lines)

#     await callback.message.edit_text(
#         new_text, reply_markup=get_callback_btns(btns=main_btns)
#     )
#     await state.update_data(lines=lines)


@router.callback_query(F.data == "add_bold")
async def add_bold(callback: CallbackQuery, state: FSMContext):
    lines = await state.get_value("lines")
    numbered_lines = [f"{line}" for i, line in enumerate(lines)]
    btns = {}

    for count, line in enumerate(numbered_lines):
        btns[line] = f"add_bold_{count}"
    
    btns["Назад"] = "back"

    await callback.message.edit_text(
        "Виберіть рядок 👇", reply_markup=get_callback_btns(btns=btns, sizes=(1,))
    )


class BoldState(StatesGroup):
    words = State()


@router.callback_query(F.data.startswith("add_bold_"))
async def add_bold(callback: CallbackQuery, state: FSMContext):
    line_number = int(callback.data.split("_")[-1])
    lines = await state.get_value("lines")

    await state.update_data(line_number=line_number)
    await callback.message.edit_text(
        f"Введіть слова, які треба виділити жирним 👇\n\n<code>{lines[line_number]}</code>"
    )
    await state.set_state(BoldState.words)


@router.message(BoldState.words)
async def add_bold(message: Message, state: FSMContext):
    lines = await state.get_value("lines")
    line_number = await state.get_value("line_number")
    words = message.text

    old_line = lines[line_number]
    new_line = old_line.replace(words, f"<b>{words}</b>", 1)
    lines[line_number] = new_line

    new_text = "\n".join(lines)

    await message.answer(new_text, reply_markup=get_callback_btns(btns=main_btns))
    await state.update_data(lines=lines)
