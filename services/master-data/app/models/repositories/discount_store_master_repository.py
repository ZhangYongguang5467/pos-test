# Copyright 2025 masa@kugel  # # Licensed under the Apache License, Version 2.0 (the "License");  # you may not use this file except in compliance with the License.  # You may obtain a copy of the License at  # #     http://www.apache.org/licenses/LICENSE-2.0  # # Unless required by applicable law or agreed to in writing, software  # distributed under the License is distributed on an "AS IS" BASIS,  # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  # See the License for the specific language governing permissions and  # limitations under the License.
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.documents.discount_store_master_document import DiscountStoreMasterDocument
from kugel_common.models.repositories.abstract_repository import AbstractRepository
from app.config.settings import settings
from kugel_common.schemas.pagination import PaginatedResult

from logging import getLogger

logger = getLogger(__name__)


class DiscountStoreMasterRepository(AbstractRepository[DiscountStoreMasterDocument]):
    """
    Repository for managing discount master data in the database.

    Provides CRUD operations and pagination for discount store records,
    with automatic tenant scoping for multi-tenant support.
    This repository is used by the discount service to manage discount master data.
    """

    def __init__(self, db: AsyncIOMotorDatabase, tenant_id: str):
        """
        Initialize a new DiscountStoreMasterRepository instance.

        Args:
            db: MongoDB database instance.
            tenant_id: Identifier for the tenant whose data this repository will manage.
        """
        super().__init__(settings.DB_COLLECTION_NAME_DISCOUNT_MASTER, DiscountStoreMasterDocument, db)
        self.tenant_id = tenant_id

    async def create_discount_store_async(self, document: DiscountStoreMasterDocument) -> DiscountStoreMasterDocument:
        """
        Create a new discount store in the database.

        Automatically assigns the repository's tenant_id and generates a shard key.

        Args:
            document: DiscountStoreMasterDocument to create.

        Returns:
            The created discount store document.

        Raises:
            Exception: If creation fails.
        """
        document.tenant_id = self.tenant_id
        document.shard_key = self.__get_shard_key(document)
        success = await self.create_async(document)
        if success:
            return document
        else:
            raise Exception("Failed to create discount store")

    async def get_discount_store_by_code_async(self, discount_code: str) -> DiscountStoreMasterDocument:
        """
        Retrieve a discount store by its unique code.

        Args:
            discount_code: Unique identifier for the discount.

        Returns:
            DiscountStoreMasterDocument if found, else None.
            """
        return await self.get_one_async(self.__make_query_filter(discount_code))

    async def get_discount_store_by_filter_async(
        self, query_filter: dict, limit: int, page: int, sort: list[tuple[str, int]]
    ) -> list[DiscountStoreMasterDocument]:
        """
        Retrieve discount store record matching the specified filter with pagination and sorting.

        This method automatically adds tenant filtering to ensure data isolation.

        Args:
            query_filter: MongoDB query filter to select categories
            limit: Maximum number of categories to return per page
            page: Page number (1-based) to retrieve
            sort: List of tuples containing field name and sort direction

        Returns:
            List of category documents matching the query parameters
        """
        query_filter["tenant_id"] = self.tenant_id
        logger.debug(f"query_filter: {query_filter} limit: {limit} page: {page} sort: {sort}")
        return await self.get_list_async_with_sort_and_paging(query_filter, limit, page, sort)

    async def get_discount_store_by_filter_paginated_async(
        self, query_filter: dict, limit: int, page: int, sort: list[tuple[str, int]]
    ) -> PaginatedResult[DiscountStoreMasterDocument]:
        """
        Retrieve discount store records matching the filter with pagination and sorting.

        Automatically adds tenant filtering. External query_filter dict is not modified.

        Args:
            query_filter: MongoDB query filter
            limit: Max number of documents
            page: Page number (1-based)
            sort: List of tuples (field, direction), direction: 1=asc, -1=desc

        Returns:
            List of DiscountStoreMasterDocument (or PaginatedResult for paginated version)
        """
        query_filter["tenant_id"] = self.tenant_id
        logger.debug(f"query_filter: {query_filter} limit: {limit} page: {page} sort: {sort}")
        return await self.get_paginated_list_async(query_filter, limit, page, sort)

    async def update_discount_store_async(self, discount_code: str, update_data: dict) -> DiscountStoreMasterDocument:
        """
        Update specific fields of a discount store document.

        Args:
            discount_code: Unique identifier for the discount to update.
            update_data: Dictionary containing fields to update.

        Returns:
            The updated DiscountStoreMasterDocument.

        Raises:
            Exception: If the update operation fails.
        """
        success = await self.update_one_async(self.__make_query_filter(discount_code), update_data)
        if success:
            return await self.get_discount_store_by_code_async(discount_code)
        else:
            raise Exception(f"Failed to update discount with code {discount_code}")

    async def replace_discount_store_async(
        self, discount_code: str, new_document: DiscountStoreMasterDocument
    ) -> DiscountStoreMasterDocument:
        """
        Replace an existing discount with a new document.

        Args:
            discount_code: Unique identifier for the category to replace
            new_document: New discount document to replace the existing one

        Returns:
            The replaced discount document
        """
        success = await self.replace_one_async(self.__make_query_filter(discount_code), new_document)
        if success:
            return new_document
        else:
            raise Exception(f"Failed to replace discount with code {discount_code}")

    async def delete_discount_store_async(self, discount_code: str):
        """
        Delete a category from the database.

        Args:
            discount_code: Unique identifier for the discount_code to delete

        Returns:
            None
        """
        return await self.delete_async(self.__make_query_filter(discount_code))

    def __make_query_filter(self, discount_code: str) -> dict:
        """
        Create a query filter for discount store operations based on tenant and discount code.

        Args:
            discount_code: Unique identifier for the discount store.

        Returns:
            Dictionary containing tenant_id and discount_code for MongoDB query.
        """
        return {"tenant_id": self.tenant_id, "discount_code": discount_code}

    def __get_shard_key(self, document: DiscountStoreMasterDocument) -> str:
        """
        Generate a shard key for the discount store document.

        Currently uses only the tenant ID. Consider adding discount_code for uniqueness.

        Args:
            document: DiscountStoreMasterDocument

        Returns:
            String representation of the shard key.
        """
        keys = []
        keys.append(document.tenant_id)
        return "-".join(keys)
