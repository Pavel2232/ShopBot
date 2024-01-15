import os
from typing import Awaitable, Dict, Callable, Any
from aiogram.types import TelegramObject
from aiogram import BaseMiddleware
from strapi import Strapi


class StrapiCartsMiddleware(BaseMiddleware):
    """Dependency injection instance Strapi"""
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:

        data['strapi'] = Strapi(
            token=os.getenv('STRAPI_PRODUCT_TOKEN'),
            api_url=os.getenv('API_STRAPI_URL')
        )

        return await handler(event, data)
