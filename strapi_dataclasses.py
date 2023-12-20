from typing import Optional
from pydantic import BaseModel


class ProductImageSize(BaseModel):
    hash: str
    name: str
    url: str


class ProductImageParams(BaseModel):
    small: ProductImageSize


class ProductImage(BaseModel):
    formats: ProductImageParams


class ProductImageList(BaseModel):
    attributes: ProductImage


class ProductPictures(BaseModel):
    data: list[ProductImageList]


class ProductAttributes(BaseModel):
    title: str
    description: str
    price: int
    state: str
    picture: Optional[ProductPictures] | None = None


class Products(BaseModel):
    id: int
    attributes: ProductAttributes


class ProductStrapiModelList(BaseModel):
    data: list[Products]


class ProductStrapiModel(BaseModel):
    data: Products


class QuantityProductsCartAttributes(BaseModel):
    quantity: int
    product: Optional[ProductStrapiModel] | None = None


class QuantityProductsAttributes(BaseModel):
    id: int
    attributes: QuantityProductsCartAttributes


class QuantityProductsModelList(BaseModel):
    data: list[QuantityProductsAttributes]


class QuantityProductsModel(BaseModel):
    data: QuantityProductsAttributes


class CartAttributes(BaseModel):
    id_tg: int
    quantity_products: Optional[QuantityProductsModelList] | None = None


class CartList(BaseModel):
    id: int
    attributes: CartAttributes


class ShoppingCartStrapiModel(BaseModel):
    data: CartList


class ShoppingCartStrapiModelList(BaseModel):
    data: list[CartList]
