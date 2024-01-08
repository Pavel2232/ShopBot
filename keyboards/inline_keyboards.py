import os
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from callbackdata_factory.callbacks import (ProductCallback, BackCallback,
                                            AddToShoppingCartCallback,
                                            RemoveProductCartCallback,
                                            MyShoppingCartCallback,
                                            PayCallback,
                                            PaginatorCallback)
from strapi_model import ShoppingCartStrapiModelList, ProductStrapiModelList


async def create_catalog_inlines(
        products: ProductStrapiModelList,
        id_user: int,
        end_page: int,
        current_page: int = 1,
        start_page: int = 0) -> InlineKeyboardMarkup:
    markup = InlineKeyboardBuilder()
    pagination_markup = InlineKeyboardBuilder()

    last_page = len(products.data) // int(os.getenv('PAGINATION')) + 1

    for product in products.data[start_page:end_page]:
        markup.button(text='{}'.format(product.attributes.title),
                      callback_data=ProductCallback(id=product.id))

    markup.button(
        text='Моя корзина 🛍️',
        callback_data=MyShoppingCartCallback(
            id_user=id_user
        )
    )

    pagination_markup.button(
        text='Назад',
        callback_data=PaginatorCallback(
            current_page=current_page,
            last_page=last_page,
            start_page=start_page,
            end_page=end_page,
            next=False,
            back=True
        ))

    pagination_markup.button(text='{current_page}/{last_page}'.format(
        current_page=current_page,
        last_page=last_page
        ),
        callback_data='None')

    pagination_markup.button(text='Следующая',
                             callback_data=PaginatorCallback(
                                 current_page=current_page,
                                 start_page=start_page,
                                 last_page=last_page,
                                 end_page=end_page,
                                 next=True,
                                 back=False
                             )
                             )

    markup.adjust(1, repeat=True)

    pagination_markup.adjust(3)

    buttons = [keyboard for keyboard in pagination_markup.buttons]

    markup.row(*buttons)

    return markup.as_markup()


def return_back_and_cart_button(
        id_product: int,
        id_user: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardBuilder()

    markup.button(
        text='Добавить в корзину',
        callback_data=AddToShoppingCartCallback(
            id_product=id_product
        )
    )
    markup.button(
        text='Назад',
        callback_data=BackCallback(back=True)
    )
    markup.button(
        text='Моя корзина 🛍',
        callback_data=MyShoppingCartCallback(
            id_user=id_user
        )
    )
    markup.adjust(2)
    return markup.as_markup()


def remove_product_cart(id_user: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardBuilder()

    markup.button(
        text='Моя корзина 🛍',
        callback_data=MyShoppingCartCallback(
            id_user=id_user
        )
    )
    markup.button(
        text='Назад',
        callback_data=BackCallback(back=True)
    )
    return markup.as_markup()


def working_with_cart(
        cart_products: ShoppingCartStrapiModelList) -> InlineKeyboardMarkup:
    markup = InlineKeyboardBuilder()
    products_ids = []
    for cart in cart_products.data:
        for product_quantity in cart.attributes.quantity_products.data:
            products_ids.append(
                (
                    product_quantity.id,
                    product_quantity.attributes.product.data.attributes.title
                )
            )
    for product_quantity_id, title in products_ids:
        markup.button(
            text='Убрать {title}'.format(title=title),
            callback_data=RemoveProductCartCallback(
                remove_id_quantity_product=product_quantity_id
            )
        )

    markup.button(
        text='Оплатить',
        callback_data=PayCallback(pay=True)
    )

    markup.button(
        text='В меню',
        callback_data=BackCallback(back=True)
    )

    markup.adjust(1, 1, 1, 2)
    return markup.as_markup()
