from aiogram.filters.callback_data import CallbackData


class ProductCallback(CallbackData, prefix='Product'):
    id: int


class BackCallback(CallbackData, prefix='Back'):
    back: bool


class AddToShoppingCartCallback(CallbackData, prefix='Cart'):
    id_product: int


class RemoveProductCartCallback(CallbackData, prefix='Remove'):
    remove_id_quantity_product: int


class MyShoppingCartCallback(CallbackData, prefix='Shopping_cart'):
    id_user: int


class PayCallback(CallbackData, prefix='pay'):
    pay: bool


class PaginatorCallback(CallbackData, prefix='page_'):
    start_page: int
    end_page: int
    current_page: int
    last_page: int
    next: bool
    back: bool
