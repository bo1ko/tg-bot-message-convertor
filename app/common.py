from aiogram.types import BotCommand


private = [
    BotCommand(command='start', description='Запустити бота'),
    BotCommand(command='list', description='Список каналів'),
    BotCommand(command='add_channel', description='Додати канал'),
    BotCommand(command='remove_channel', description='Видалити канал'),
]