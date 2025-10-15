# Copyright 2025 masa@kugel  # # Licensed under the Apache License, Version 2.0 (the "License");  # you may not use this file except in compliance with the License.  # You may obtain a copy of the License at  # #     http://www.apache.org/licenses/LICENSE-2.0  # # Unless required by applicable law or agreed to in writing, software  # distributed under the License is distributed on an "AS IS" BASIS,  # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  # See the License for the specific language governing permissions and  # limitations under the License.
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.documents.category_discount_master_document import CategoryDiscountMasterDocument
from kugel_common.models.repositories.abstract_repository import AbstractRepository
from app.config.settings import settings
from kugel_common.schemas.pagination import PaginatedResult

from logging import getLogger

logger = getLogger(__name__)


class CategoryDiscountMasterRepository(AbstractRepository[CategoryDiscountMasterDocument]):
    """
    Repository for managing category discount master data in the database.

    This class provides specific implementation for CRUD operations on category discount master data,
    extending the generic functionality provided by AbstractRepository. It handles
    tenant-specific data access and includes methods tailored for category operations.
    """

    def __init__(self, db: AsyncIOMotorDatabase, tenant_id: str):
        """
        Initialize a new CategoryDiscountMasterRepository instance.

        Args:
            db: MongoDB database instance
            tenant_id: Identifier for the tenant whose data this repository will manage
        """
        super().__init__(settings.DB_COLLECTION_NAME_CATEGORY_DISCOUNT_MASTER, CategoryDiscountMasterDocument, db)
        self.tenant_id = tenant_id

    async def create_category_discount_async(self, document: CategoryDiscountMasterDocument) -> CategoryDiscountMasterDocument:
        """
        Create a new category Discount in the database.

        This method sets the tenant ID and generates a shard key before creating the document.

        Args:
            document: Category Discount document to create

        Returns:
            The created category Discount document
        """
        document.tenant_id = self.tenant_id
        document.shard_key = self.__get_shard_key(document)
        success = await self.create_async(document)
        if success:
            return document
        else:
            raise Exception("Failed to create category discount")

    async def get_category_discount_by_code_async(self, category_code: str) -> CategoryDiscountMasterDocument:
        """
        Retrieve a category discount by its unique code.

        Args:
            category_code: Unique identifier for the category

        Returns:
            The matching category discount document, or None if not found
        """
        return await self.get_one_async(self.__make_query_filter(category_code))

    async def get_category_discount_by_filter_async(
        self, query_filter: dict, limit: int, page: int, sort: list[tuple[str, int]]
    ) -> list[CategoryDiscountMasterDocument]:
        """
        Retrieve categories matching the specified filter with pagination and sorting.

        This method automatically adds tenant filtering to ensure data isolation.

        Args:
            query_filter: MongoDB query filter to select categories
            limit: Maximum number of categories to return per page
            page: Page number (1-based) to retrieve
            sort: List of tuples containing field name and sort direction

        Returns:
            List of category dicount documents matching the query parameters
        """
        query_filter["tenant_id"] = self.tenant_id
        logger.debug(f"query_filter: {query_filter} limit: {limit} page: {page} sort: {sort}")
        return await self.get_list_async_with_sort_and_paging(query_filter, limit, page, sort)

    async def get_category_discount_by_filter_paginated_async(
        self, query_filter: dict, limit: int, page: int, sort: list[tuple[str, int]]
    ) -> PaginatedResult[CategoryDiscountMasterDocument]:
        """
        Retrieve categories matching the specified filter with pagination metadata.

        This method automatically adds tenant filtering to ensure data isolation and
        returns both the data and pagination metadata.

        Args:
            query_filter: MongoDB query filter to select categories
            limit: Maximum number of categories to return per page
            page: Page number (1-based) to retrieve
            sort: List of tuples containing field name and sort direction

        Returns:
            PaginatedResult containing category dicount documents and metadata
        """
        query_filter["tenant_id"] = self.tenant_id
        logger.debug(f"query_filter: {query_filter} limit: {limit} page: {page} sort: {sort}")
        return await self.get_paginated_list_async(query_filter, limit, page, sort)

    async def update_category_discount_async(self, category_code: str, update_data: dict) -> CategoryDiscountMasterDocument:
        """
        Update specific fields of a category dicount.

        Args:
            category_code: Unique identifier for the category to update
            update_data: Dictionary containing the fields to update and their new values

        Returns:
            The updated category dicount document
        """
        success = await self.update_one_async(self.__make_query_filter(category_code), update_data)
        if success:
            return await self.get_category_discount_by_code_async(category_code)
        else:
            raise Exception(f"Failed to update category discount with code {category_code}")

    async def replace_category_discount_async(
        self, category_code: str, new_document: CategoryDiscountMasterDocument
    ) -> CategoryDiscountMasterDocument:
        """
        Replace an existing category dicount with a new document.

        Args:
            category_code: Unique identifier for the category to replace
            new_document: New category dicount document to replace the existing one

        Returns:
            The replaced category dicount document
        """
        success = await self.replace_one_async(self.__make_query_filter(category_code), new_document)
        if success:
            return new_document
        else:
            raise Exception(f"Failed to replace category with code {category_code}")

    async def delete_category_discount_async(self, category_code: str):
        """
        Delete a category discount from the database.

        Args:
            category_code: Unique identifier for the category to delete

        Returns:
            None
        """
        return await self.delete_async(self.__make_query_filter(category_code))

    def __make_query_filter(self, category_code: str) -> dict:
        """
        Create a query filter for category discount operations based on tenant and category code.

        This private method ensures that all queries are scoped to the correct tenant.

        Args:
            category_code: Unique identifier for the category

        Returns:
            Dictionary containing the query filter parameters
        """
        return {"tenant_id": self.tenant_id, "category_code": category_code}

    def __get_shard_key(self, document: CategoryDiscountMasterDocument) -> str:
        """
        Generate a shard key for the category discount document.

        Currently uses only the tenant ID as the sharding key.

        Args:
            document: Category discount document for which to generate a shard key

        Returns:
            String representation of the shard key
        """
        keys = []
        keys.append(document.tenant_id)
        return "-".join(keys)
