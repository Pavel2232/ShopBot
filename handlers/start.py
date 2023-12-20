import os
import textwrap
from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from pydantic import validate_email
from pydantic_core import PydanticCustomError
from callbackdata_class.callback_class import ProductCallback, BackCallback, AddToShoppingCartCallback, \
    MyShoppingCartCallback, RemoveProductCartCallback, PayCallback, PaginatorCallback
from keyboards.inline_keyboards import create_catalog_inlines, return_back_and_cart_button, remove_product_cart, \
    working_with_cart
from keyboards.reply_keyboards import get_check_email_keyboards
from settings_bot.command_menu import set_commands
from strapi_class_api import Strapi

shop = Router(name=__name__)


class UserShopping(StatesGroup):
    start = State()
    handle_menu = State()
    handle_description = State()
    handle_cart = State()
    waiting_email = State()
    confirm_email = State()


@shop.message(CommandStart())
async def start_shopping(message: Message, state: FSMContext) -> None:
    await set_commands(message.bot)
    await state.set_state(UserShopping.start)
    await message.answer(
        'Пожалуйста выберите:', reply_markup=await create_catalog_inlines(
            id_user=message.from_user.id,
            current_page=1,
            start_page=0,
            end_page=int(os.getenv('PAGINATION'))
        ))


@shop.callback_query(ProductCallback.filter())
async def detail_product(call: CallbackQuery, callback_data: ProductCallback, state: FSMContext):
    strapi = Strapi(
        token=os.getenv('STRAPI_PRODUCT_TOKEN'),
        api_url=os.getenv('API_STRAPI_URL'),
        endpoints='products',
    )

    product = await strapi.async_get_product_by_id(callback_data.id)

    await call.message.answer_photo(BufferedInputFile(
        await strapi.async_photo_bytes(callback_data.id),
        filename='{}.jpeg'.format(product.data.attributes.title)),
        caption=textwrap.dedent(
            '''{title}  - {price}руб.
        
{description}
'''.format(
                title=product.data.attributes.title,
                price=product.data.attributes.price,
                description=product.data.attributes.description)),
        reply_markup=return_back_and_cart_button(callback_data.id, call.from_user.id))

    await state.set_state(UserShopping.handle_menu)


@shop.callback_query(AddToShoppingCartCallback.filter())
async def add_shopping_cart(call: CallbackQuery, callback_data: AddToShoppingCartCallback):
    strapi = Strapi(
        token=os.getenv('STRAPI_PRODUCT_TOKEN'),
        api_url=os.getenv('API_STRAPI_URL'),
        endpoints='carts')

    await strapi.async_create_with_relation(
        product_id=callback_data.id_product,
        user_id=call.from_user.id,
        data_model={
            'data': {
                'id_tg': call.from_user.id,
            }
        },
        name_relation='quantity-products',
        field_relation='quantity_products',
        data_relation={'data': {
            'product': callback_data.id_product,
            'quantity': 2,
        }
        })
    await call.answer('Добавлен  в корзину')

    await call.message.edit_reply_markup(reply_markup=remove_product_cart(call.from_user.id))


@shop.callback_query(MyShoppingCartCallback.filter())
async def get_my_shopping_cart(call: CallbackQuery, callback_data: MyShoppingCartCallback, state: FSMContext):
    strapi = Strapi(
        token=os.getenv('STRAPI_PRODUCT_TOKEN'),
        api_url=os.getenv('API_STRAPI_URL'),
        endpoints='carts')

    all_products = await strapi.async_get_cart_by_filter(
        filter=str(callback_data.id_user),
        filter_field='id_tg')
    products = []
    total_price = []
    for product_list in all_products.data:
        for product in product_list.attributes.quantity_products.data:
            products.append(
                (
                    product.attributes.product.data.attributes.title,
                    product.attributes.quantity,
                    product.attributes.product.data.attributes.price,
                )
            )
            total_price.append(product.attributes.quantity * product.attributes.product.data.attributes.price)
        await state.update_data(id_cart=product_list.id)
    answer = '''
    Товары в корзине:
    
'''
    for name_product, quantity, price in products:
        answer += textwrap.dedent(('''{title}
Количество: {quantity} * {price} = {total_price}


'''.format(
            title=name_product,
            quantity=quantity,
            price=price,
            total_price=quantity * price)))
    total_price = sum(total_price)
    answer += textwrap.dedent('Итог: {total_price}'.format(total_price=total_price))
    await state.update_data(total_price=total_price)
    await call.message.answer(text=answer, reply_markup=working_with_cart(all_products))
    await state.set_state(UserShopping.handle_cart)


@shop.callback_query(RemoveProductCartCallback.filter())
async def remove_product_shopping_cart(call: CallbackQuery, callback_data: RemoveProductCartCallback,
                                       state: FSMContext):
    strapi = Strapi(
        token=os.getenv('STRAPI_PRODUCT_TOKEN'),
        api_url=os.getenv('API_STRAPI_URL'),
        endpoints='quantity-products')

    await strapi.async_deleted_product(callback_data.remove_id_quantity_product)
    await call.answer('Продукт убран из корзины')
    await get_my_shopping_cart(call, MyShoppingCartCallback(id_user=call.from_user.id), state)


@shop.callback_query(PayCallback.filter())
async def survey_user(call: CallbackQuery,
                      state: FSMContext):
    await call.message.answer('Введите вашу почту')
    await state.set_state(UserShopping.waiting_email)


@shop.message(UserShopping.waiting_email)
async def get_email(message: Message, state: FSMContext):
    try:
        validate_email(message.text)
        await state.set_state(UserShopping.confirm_email)
        await message.answer(textwrap.dedent(
            '''Проверьте правильность почты:
{email}'''.format(
                email=message.text
            )
        ), reply_markup=get_check_email_keyboards())
    except PydanticCustomError:
        await message.answer(textwrap.dedent('''
Некорректная почта.
Введите почту в формате: user@mail.ru''')
                             )


@shop.message(UserShopping.confirm_email)
async def check_email_finish_step(message: Message, state: FSMContext):
    strapi = Strapi(
        token=os.getenv('STRAPI_PRODUCT_TOKEN'),
        api_url=os.getenv('API_STRAPI_URL'),
        endpoints='carts')

    data_order = await state.get_data()

    if message.text == 'Да':
        await strapi.async_unpublished_cart(data_order.get('id_cart'))
        await state.clear()
        await state.set_state(UserShopping.start)
        await message.answer('''
Спасибо за заказ!
Ожидайте подтверждения по почте!''')
        await start_shopping(message, state)
    else:
        await message.answer('Введите вашу почту')
        await state.set_state(UserShopping.waiting_email)


@shop.callback_query(PaginatorCallback.filter())
async def pagination_page(call: CallbackQuery, callback_data: PaginatorCallback):
    start = callback_data.start_page
    end = callback_data.end_page
    current_page = callback_data.current_page
    last_page = callback_data.last_page

    if callback_data.next:
        if current_page != last_page:
            start = end
            end += int(os.getenv('PAGINATION'))
            current_page += 1
            await call.answer()
        else:
            current_page = last_page
            await call.answer('Это последняя страница')

    if callback_data.back:
        if current_page != 1:
            end = start
            start -= int(os.getenv('PAGINATION'))
            current_page -= 1
            await call.answer()
        else:
            current_page = 1
            await call.answer('Вы в начале')

    try:
        await call.message.edit_reply_markup(
            reply_markup=await create_catalog_inlines(
                id_user=call.from_user.id,
                current_page=current_page,
                start_page=start,
                end_page=end
            ))
    except TelegramBadRequest:
        pass


@shop.callback_query(BackCallback.filter())
async def back_menu(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=await create_catalog_inlines(
        id_user=call.from_user.id,
        current_page=1,
        start_page=0,
        end_page=int(os.getenv('PAGINATION')
                     )
    )
                                         )

    await state.set_state(UserShopping.handle_description)
