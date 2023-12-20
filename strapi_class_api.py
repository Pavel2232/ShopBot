from aiogram.client.session import aiohttp

from strapi_dataclasses import (
    ProductStrapiModelList,
    ProductStrapiModel, ShoppingCartStrapiModel,
    QuantityProductsModelList,
    QuantityProductsModel, ShoppingCartStrapiModelList)


class Strapi:

    def __init__(self,
                 token: str,
                 endpoints: str,
                 api_url='http://localhost:1337/api/') -> None:
        """

        :param token: secret token from strapi settings
        :param api_url: default 'http://localhost:1337/api/' for dev environments
        :type int
        :param endpoints:
        """
        self._headers = {'Authorization': 'bearer {}'.format(token)}
        self._api_url = api_url
        self._endpoints = endpoints
        self._endpoint = self._endpoints[:-1]

    async def async_get_product_all(self) -> ProductStrapiModelList:
        """Receives API request data, returns class StrapiModelList."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url='{api_url}{endpoints}'.format(
                        api_url=self._api_url,
                        endpoints=self._endpoints),
                    headers=self._headers) as response:
                list_object = await response.json()
                model_strapi = ProductStrapiModelList(**list_object)
                return model_strapi

    async def async_get_product_by_id(self, id_objects: int) -> ProductStrapiModel:
        """
        Get model object by id model
        :param id_objects: id endpoints your request
        :return: class StrapiModel
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url='{api_url}{endpoints}/{id}?populate=*'.format(
                        api_url=self._api_url,
                        endpoints=self._endpoints,
                        id=id_objects),
                    headers=self._headers) as response:
                list_object = await response.json()
                model_strapi = ProductStrapiModel(**list_object)
                return model_strapi

    async def async_get_cart_by_id(self, id_objects: int) -> ShoppingCartStrapiModel:
        """
        Get model object by id model
        :param id_objects: id endpoints your request
        :return: class StrapiModel
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url='{api_url}{endpoints}/{id}?populate[quantity_products][populate][0]=product'.format(
                        api_url=self._api_url,
                        endpoints=self._endpoints,
                        id=id_objects),
                    headers=self._headers) as response:
                list_object = await response.json()
                model_strapi = ShoppingCartStrapiModel(**list_object)
                return model_strapi

    async def async_get_cart_by_filter(self, filter_field: str, filter: str) -> ShoppingCartStrapiModelList:
        """
        Get ShoppingCartStrapiModelList from endpoints strapi by filter_field in model and filter param
        :param filter_field: name search field in model strapi
        :param filter: the value of which will be equal to the filtering field
        :return: ShoppingCartStrapiModelList(BaseModel)
        """
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                url='{api_url}{endpoints}?populate[quantity_products][populate][0]=product'
                    '&filters[{filter_field}][$eq]={filter}'.format(
                        api_url=self._api_url,
                        endpoints=self._endpoints,
                        filter_field=filter_field,
                        filter=filter),
                headers=self._headers)
            cart = await response.json()
            strapi_model = ShoppingCartStrapiModelList(**cart)
            return strapi_model

    async def async_photo_bytes(self, id_objects: int) -> bytes:
        """
        generates image bytes from a request
        :param id_objects: id model
        :return: bytes
        """
        product_model = await self.async_get_product_by_id(id_objects)
        for product in product_model.data.attributes.picture.data:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        url='http://localhost:1337''{url}'.format(url=product.attributes.formats.small.url),
                        headers=self._headers) as response:
                    picture_bytes = await response.content.read()
                    return picture_bytes

    async def async_create_with_relation(
            self, product_id: int,
            user_id: int, data_model: dict,
            name_relation: str, data_relation: dict,
            field_relation: str) -> None:
        """
        creates a main model with related models

        :param product_id: product id by database
        :param user_id: telegram id user
        :param data_model: data format json {
            'data': {
                'field_model': values,
            }
        }
        :param name_relation: field linked with your main model
        :param data_relation: data formats json {
        'data': {
            'your_field': value,
        }
        :param field_relation: name of the associated field
        :return: None
        """
        async with aiohttp.ClientSession() as session:
            shop_cart_response = await session.get(
                url='{api_url}{endpoints}?populate[{field_relation}][populate][0]=product'
                    '&filters[id_tg][$eq]={user_id}'.format(
                        api_url=self._api_url,
                        endpoints=self._endpoints,
                        field_relation=field_relation,
                        user_id=user_id
                    ),
                headers=self._headers)
            shop_cart = await shop_cart_response.json()
            if not shop_cart.get('data'):
                response = await session.post(
                    url='{api_url}{relation_endpoints}'.format(
                        api_url=self._api_url,
                        relation_endpoints=name_relation),
                    headers=self._headers,
                    json=data_relation)

                quantity = await response.json()
                quantity_product = QuantityProductsModel(**quantity)
                quantity_id = quantity_product.data.id
                data_model.get('data')[field_relation] = quantity_id
                await session.post(
                    url='{api_url}{endpoints}'.format(
                        api_url=self._api_url,
                        endpoints=self._endpoints),
                    headers=self._headers,
                    json=data_model
                )
            else:
                quantity_product_request = await session.get(
                    url='{api_url}{relation_endpoint}?populate[{product}][populate][0]=id'
                        '&filters[{cart}][id][$eq]={search_id}'.format(
                            api_url=self._api_url,
                            relation_endpoint=name_relation,
                            product='product',
                            cart=self._endpoint,
                            search_id=shop_cart.get('data')[0].get('id')),
                    headers=self._headers)

                quantity_product_response = await quantity_product_request.json()
                quantity_product = QuantityProductsModelList(**quantity_product_response)
                quantity_product_id = 0
                for id_product_by_cats in quantity_product.data:
                    if id_product_by_cats.attributes.product.data.id == product_id:
                        quantity_product_id = id_product_by_cats.id

            if quantity_product_id:
                await session.put(
                    url='{api_url}{relation_endpoints}/{id}'.format(
                        api_url=self._api_url,
                        relation_endpoints=name_relation,
                        id=quantity_product_id
                    ),
                    headers=self._headers,
                    json=data_relation)

            else:
                request = await session.post(
                    url='{api_url}{relation_endpoints}'.format(
                        api_url=self._api_url,
                        relation_endpoints=name_relation),
                    headers=self._headers,
                    json=data_relation)

                quantity = await request.json()
                quantity_product = QuantityProductsModel(**quantity)
                quantity_id = quantity_product.data.id
                data_model.get('data')[field_relation] = {
                    'connect': [quantity_id]
                }

                await session.put(
                    url='{api_url}{endpoints}/{id}'.format(
                        api_url=self._api_url,
                        endpoints=self._endpoints,
                        id=shop_cart.get('data')[0].get('id')
                    ),
                    headers=self._headers,
                    json=data_model
                )

    async def async_deleted_product(self, id_object: int) -> None:
        """
        Deleted object from strapi
        :param id_object: id product_quantity model
        :return: None
        """
        async with aiohttp.ClientSession() as session:
            await session.delete(
                url='{api_url}{endpoints}/{id}'.format(
                    api_url=self._api_url,
                    endpoints=self._endpoints,
                    id=id_object),
                headers=self._headers)

    async def async_create_order_user(self, email: str, id_cart: int, total_price: int) -> bool:
        """
        Create Order if not Order no active (unpublished order)
        :param email: email user
        :param id_cart: id shopping cart user
        :param total_price: sum Order
        :return: True if create order, False if order has already
        """
        async with aiohttp.ClientSession() as session:
            order_response = await session.get(
                url='{api_url}{endpoints}?filters[email][$eq]={email}'.format(
                    api_url=self._api_url,
                    endpoints=self._endpoints,
                    email=email
                ),
                headers=self._headers)
            order = await order_response.json()
            if not order.get('data'):
                data_order = {
                    'data': {
                        'cart': id_cart,
                        'email': email,
                        'total_price': total_price,
                    }
                }
                await session.post(
                    url='{api_url}{endpoints}'.format(
                        api_url=self._api_url,
                        endpoints=self._endpoints,
                    ),
                    headers=self._headers,
                    json=data_order)
                return True
            return False

    async def async_unpublished_cart(self, id_cart: int) -> None:
        """
        Completing the active cart
        :param id_cart: id cart user
        :return: None
        """
        async with aiohttp.ClientSession() as session:
            data_cart = {
                'data': {
                    'publishedAt': None
                }
            }
            await session.put(
                url='{api_url}{endpoints}/{id}?populate=*'.format(
                    api_url=self._api_url,
                    endpoints=self._endpoints,
                    id=id_cart),
                headers=self._headers,
                json=data_cart)
