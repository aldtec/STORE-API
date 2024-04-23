from typing import List
from uuid import UUID
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo
from store.db.mongo import db_client
from store.models.product import ProductModel
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut
from store.core.exceptions import NotFoundException


class ProductUsecase:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient = db_client.get()
        self.database: AsyncIOMotorDatabase = self.client.get_database()
        self.collection = self.database.get_collection("products")

    async def create(self, body: ProductIn) -> ProductOut:
        product_model = ProductModel(**body.model_dump())
        await self.collection.insert_one(product_model.model_dump())

        return ProductOut(**product_model.model_dump())

    async def get(self, id: UUID) -> ProductOut:
        result = await self.collection.find_one({"id": id})

        if not result:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        return ProductOut(**result)

    async def query(self) -> List[ProductOut]:
        return [ProductOut(**item) async for item in self.collection.find()]
    
    # Coloquei sem indice mesmo pois é um projeto pequeno
    async def query_nome(self, name: str) -> List[ProductOut]:
        result = await self.collection.find({"name": {"$regex": f"/{name}/i"}})
        if not result:
            raise NotFoundException(message=f"Product not found with name: {id}")
        return ProductOut(**result)
 
    async def update(self, id: UUID, body: ProductUpdate) -> ProductUpdateOut:
        result = await self.collection.find_one_and_update(
            filter={"id": id},
            update={"$set": body.model_dump(exclude_none=True)},
            return_document=pymongo.ReturnDocument.AFTER,
        )

        return ProductUpdateOut(**result)

    async def delete(self, id: UUID) -> bool:
        product = await self.collection.find_one({"id": id})
        if not product:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        result = await self.collection.delete_one({"id": id})

        return True if result.deleted_count > 0 else False

    # Buscar um Produto por faixa de preço    
    async def query_price_range(self, min_price: float = None, max_price: float = None) -> List[ProductOut]:
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValueError(message="Minimum price cannot be greater than maximum price.")

        price_filter = {}
        if min_price is not None:
            price_filter["price"] = {"$gt | gte": min_price}  # Greater than or equal to min_price
        if max_price is not None:
            price_filter["price"] = {"$lt | lte": max_price}  # Less than or equal to max_price

        cursor = self.collection.find(filter)
        if not cursor:
            raise NotFoundException(message=f"Products not found with this range of price from {min_price} to {max_price}")
        return [ProductOut(**item) async for item in cursor]


product_usecase = ProductUsecase()
