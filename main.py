import asyncio
import logging
import os
import sys
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.redis import RedisStorage
from dotenv import load_dotenv
from handlers.shop import shop
from middliware.strapi_middleware import StrapiCartsMiddleware
from strapi import Strapi

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

    strapi_carts = Strapi(
        token=os.getenv('STRAPI_PRODUCT_TOKEN'),
        api_url=os.getenv('API_STRAPI_URL'),
        endpoints='carts')

    dp.include_router(shop)
    dp.update.middleware.register(StrapiCartsMiddleware())

    asyncio.run(dp.start_polling(bot))
