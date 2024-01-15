from aiogram.client.session import aiohttp
from strapi_model import (
    ProductStrapiModelList,
    ProductStrapiModel, ShoppingCartStrapiModel,
    QuantityProductsModelList,
    QuantityProductsModel, ShoppingCartStrapiModelList)


class BaseSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Strapi(metaclass=BaseSingleton):

    def __init__(self,
                 token: str,
                 api_url='http://localhost:1337/api/') -> None:
        """
        :param token: secret token from strapi settings
        :param api_url:
         default 'http://localhost:1337/api/' for dev environments
        """
        self._headers = {'Authorization': 'bearer {}'.format(token)}
        self._api_url = api_url
        self._session = aiohttp.ClientSession(raise_for_status=True)

    async def __aenter__(self):
        """Create session"""
        if self._session.closed:
            self._session = aiohttp.ClientSession(raise_for_status=True)
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit session"""
        await self._session.close()

    async def get_product_all(self) -> ProductStrapiModelList:
        """Receives API request data, returns class StrapiModelList."""

        async with self._session.get(
                url='{api_url}products'.format(
                    api_url=self._api_url),
                headers=self._headers) as response:
            list_object = await response.json()
            product_strapi = ProductStrapiModelList(**list_object)
            return product_strapi

    async def get_product_by_id(self, id_objects: int) -> ProductStrapiModel:
        """
        Get model object by id model
        :param id_objects: id endpoints your request
        :return: class StrapiModel
        """

        payload = {
            'populate': '*'
        }
        response = await self._session.get(
            url='{api_url}products/{id}'.format(
                api_url=self._api_url,
                id=id_objects),
            headers=self._headers,
            params=payload)
        list_object = await response.json()
        product_strapi = ProductStrapiModel(**list_object)
        return product_strapi

    async def get_cart_by_id(self, id_objects: int) -> ShoppingCartStrapiModel:
        """
        Get model object by id model
        :param id_objects: id endpoints your request
        :return: class StrapiModel
        """

        payload = {
            'populate[quantity_products][populate][0]': 'product'
        }
        response = await self._session.get(
            url='{api_url}carts/{id}'.format(
                api_url=self._api_url,
                id=id_objects),
            headers=self._headers,
            params=payload)
        list_object = await response.json()
        shopping_cart_strapi = ShoppingCartStrapiModel(**list_object)
        return shopping_cart_strapi

    async def get_cart_by_filter(self, filter_field: str,
                                 filter: str) -> ShoppingCartStrapiModelList:
        """
        Get ShoppingCartStrapiModelList from endpoints
         strapi by filter_field in model and filter param
        :param filter_field: name search field in model strapi
        :param filter: the value of which will be equal to the filtering field
        :return: ShoppingCartStrapiModelList(BaseModel)
        """

        payload = {
            'populate[quantity_products][populate][0]': 'product',
            f'filters[{filter_field}][$eq]': filter
        }
        response = await self._session.get(
            url='{api_url}carts'.format(
                api_url=self._api_url,
            ),
            headers=self._headers,
            params=payload)
        cart = await response.json()
        shopping_cart_strapi = ShoppingCartStrapiModelList(**cart)
        return shopping_cart_strapi

    async def get_photo_bytes(self, id_objects: int) -> bytes:
        """
        generates image bytes from a request
        :param id_objects: id model
        :return: bytes
        """
        url_by_photo = self._api_url.strip('api/')
        product_model = await self.get_product_by_id(id_objects)
        for product in product_model.data.attributes.picture.data:
            response = await self._session.get(
                url='{api_url}{url}'.format(
                    api_url=url_by_photo,
                    url=product.attributes.formats.small.url
                ),
                headers=self._headers)
            picture_bytes = await response.content.read()
            return picture_bytes

    async def create_user_cart(
            self, product_id: int,
            user_id: int, data_model: dict,
            data_relation: dict,
    ) -> None:
        """
        creates a cart model with product-quantity models

        :param product_id: product id by database
        :param user_id: telegram id user
        :param data_model: data format json {
            'data': {
                'field_model': values,
            }
        }
        :param data_relation: data formats json {
        'data': {
            'your_field': value,
        }
        :return: None
        """

        cart_id = await self._get_or_create_cart(
            user_id=user_id,
            data_model=data_model)

        product_quantity_id = await self._get_or_create_quantity_product(
            shop_cart_id=cart_id,
            data_model=data_model,
            data_relation=data_relation,
            product_id=product_id
        )

        await self._put_product_quantity(
            quantity_product_id=product_quantity_id,
            data_relation=data_relation
        )

    async def deleted_product(self, id_object: int) -> None:
        """
        Deleted object from strapi
        :param id_object: id product_quantity model
        :return: None
        """
        await self._session.delete(
            url='{api_url}quantity-products/{id}'.format(
                api_url=self._api_url,
                id=id_object),
            headers=self._headers)

    async def create_order_user(self, email: str, id_cart: int,
                                total_price: int) -> bool:
        """
        Create Order if not Order no active (unpublished order)
        :param email: email user
        :param id_cart: id shopping cart user
        :param total_price: sum Order
        :return: True if create order, False if order has already
        """

        payload = {'filters[email][$eq]': email}

        order_response = await self._session.get(
            url='{api_url}carts'.format(
                api_url=self._api_url,
            ),
            headers=self._headers,
            params=payload)
        order = await order_response.json()
        if order.get('data'):
            return False
        data_order = {
            'data': {
                'cart': id_cart,
                'email': email,
                'total_price': total_price,
            }
        }
        await self._session.post(
            url='{api_url}carts'.format(
                api_url=self._api_url,
            ),
            headers=self._headers,
            json=data_order)
        return True

    async def unpublished_cart(self, id_cart: int) -> None:
        """
        Completing the active cart
        :param id_cart: id cart user
        :return: None
        """

        data_cart = {
            'data': {
                'publishedAt': None
            }
        }

        payload = {'populate': '*'}

        await self._session.put(
            url='{api_url}carts/{id}'.format(
                api_url=self._api_url,
                id=id_cart),
            headers=self._headers,
            json=data_cart,
            params=payload)

    async def _get_or_create_cart(
            self, user_id: int, data_model: dict) -> int:
        """Create or get cart id"""
        payload = {
            'populate[quantity_products][populate][0]': 'product',
            'filters[id_tg][$eq]': user_id,
        }
        shop_cart_response = await self._session.get(
            url='{api_url}carts'.format(
                api_url=self._api_url,
            ),
            headers=self._headers,
            params=payload)
        shop_cart = await shop_cart_response.json()
        if not shop_cart.get('data'):
            shop_cart_response = await self._session.post(
                url='{api_url}carts'.format(
                    api_url=self._api_url,
                ),
                headers=self._headers,
                json=data_model)
            shop_cart = await shop_cart_response.json()
            return shop_cart.get('data').get('id')
        return shop_cart.get('data')[0].get('id')

    async def _get_or_create_quantity_product(
            self, shop_cart_id: int,
            data_model: dict,
            data_relation: dict,
            product_id: int) -> int:
        """Create or get quantity-product id"""
        payload = {
            'populate[product][populate][0]': 'id',
            'filters[cart][id][$eq]': shop_cart_id}

        quantity_product_request = await self._session.get(
            url='{api_url}quantity-products'.format(
                api_url=self._api_url,
            ),
            headers=self._headers,
            params=payload)

        quantity_product_response = await quantity_product_request.json()

        quantity_product = QuantityProductsModelList(
            **quantity_product_response
        )

        quantity_product_id = 0
        for id_product_by_cats in quantity_product.data:
            if id_product_by_cats.attributes.product.data.id == product_id:
                quantity_product_id = id_product_by_cats.id

        if (not quantity_product_response.get('data')
                or quantity_product_id == 0):
            quantity_product_request = await self._session.post(
                url='{api_url}quantity-products'.format(
                    api_url=self._api_url,
                ),
                headers=self._headers,
                json=data_relation)

            quantity_product_response = await quantity_product_request.json()

            quantity_product = QuantityProductsModel(
                **quantity_product_response
            )

            quantity_product_id = quantity_product.data.id

            data_model.get('data')['quantity_products'] = {
                'connect': [quantity_product_id]
            }

            await self._session.put(
                url='{api_url}carts/{cart_id}'.format(
                    api_url=self._api_url,
                    cart_id=shop_cart_id),
                headers=self._headers,
                json=data_model)

        return quantity_product_id

    async def _put_product_quantity(self, quantity_product_id: int,
                                    data_relation: dict):
        """Update quantity-product model"""
        await self._session.put(
            url='{api_url}quantity-products/{id}'.format(
                api_url=self._api_url,
                id=quantity_product_id
            ),
            headers=self._headers,
            json=data_relation)
