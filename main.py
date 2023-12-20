import asyncio
import logging
import os
import sys
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.redis import RedisStorage
from dotenv import load_dotenv
from handlers.start import shop


if __name__ == "__main__":
    load_dotenv('.env')

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        stream=sys.stdout
                        )

    storage = RedisStorage.from_url(os.getenv('REDIS_URL'))
    bot = Bot(os.getenv('TG_BOT_TOKEN'))
    dp = Dispatcher(storage=storage)

    dp.include_router(shop)

    asyncio.run(dp.start_polling(bot))


