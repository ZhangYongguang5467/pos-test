# Copyright 2025 masa@kugel  # # Licensed under the Apache License, Version 2.0 (the "License");  # you may not use this file except in compliance with the License.  # You may obtain a copy of the License at  # #     http://www.apache.org/licenses/LICENSE-2.0  # # Unless required by applicable law or agreed to in writing, software  # distributed under the License is distributed on an "AS IS" BASIS,  # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  # See the License for the specific language governing permissions and  # limitations under the License.
from logging import getLogger
from typing import Any

from kugel_common.exceptions import DocumentNotFoundException, DocumentAlreadyExistsException
from app.models.documents.category_discount_master_document import CategoryDiscountMasterDocument
from app.models.repositories.category_discount_master_repository import CategoryDiscountMasterRepository
from app.models.repositories.category_master_repository import CategoryMasterRepository
from app.models.documents.category_discount_detail_document import CategoryDiscountDetailDocument
from app.models.repositories.discount_store_master_repository import DiscountStoreMasterRepository

logger = getLogger(__name__)


class CategoryDiscountMasterService:
    """
    Service class for managing category discount master data operations.

    This service encapsulates business logic for creating, retrieving, updating,
    and deleting category-level discount records. It interacts with repository
    layers to ensure consistent access to category discount data and related
    discount store information.
    """

    def __init__(
            self, 
            category_discount_master_repo: CategoryDiscountMasterRepository,
            discount_store_master_repo: DiscountStoreMasterRepository
    ) :
        """
        Initialize the CategoryDiscountMasterService.

        Args:
            category_discount_master_repo: Repository handling category discount master data operations.
            discount_store_master_repo: Repository handling discount store master data operations.
        """
        self.category_discount_master_repo = category_discount_master_repo
        self.discount_store_master_repo =discount_store_master_repo

    async def create_category_discount_async(
        self, category_code: str, store_code:str,description: str, discount_code: str
    ) -> CategoryDiscountMasterDocument:
        """
        Create a new category discount record.

        Args:
            category_code: Unique identifier for the category.
            store_code: Store identifier where this discount applies.
            description: Detailed description of the discount.
            discount_code: Discount code associated with this category.

        Returns:
            Newly created CategoryDiscountMasterDocument.

        Raises:
            DocumentAlreadyExistsException: If a category discount with the given code already exists.
        """

        # check if category discount exists
        # Currently only category_code is used. In full implementation, store_code should also be considered.
        category = await self.category_discount_master_repo.get_category_discount_by_code_async(category_code)
        if category is not None:
            message = f"category with code {category_code} already exists. tenant_id: {category.tenant_id}"
            raise DocumentAlreadyExistsException(message, logger)

        category_discount_doc = CategoryDiscountMasterDocument()
        category_discount_doc.category_code = category_code
        category_discount_doc.store_code = store_code
        category_discount_doc.description = description
        category_discount_doc.discount_code = discount_code
        return await self.category_discount_master_repo.create_category_discount_async(category_discount_doc)

    async def get_category_discount_by_code_async(self, category_code: str) -> CategoryDiscountMasterDocument:
        """
        Retrieve a category discount by its unique code.

        Args:
            category_code: Unique identifier for the category.

        Returns:
            CategoryDiscountMasterDocument with the specified code.

        Raises:
            DocumentNotFoundException: If no category discount with the given code exists.
        """
        # Currently only category_code is used. In full implementation, store_code should also be considered.
        category = await self.category_discount_master_repo.get_category_discount_by_code_async(category_code)
        if category is None:
            message = f"category with code {category_code} not found"
            raise DocumentNotFoundException(message, logger)
        return category

    async def get_category_discount_async(self, limit: int, page: int, sort: list[tuple[str, int]]) -> list:
        """
        Retrieve a list of category discounts with pagination and sorting.

        Args:
            limit: Maximum number of records to return.
            page: Page number for pagination (1-based).
            sort: List of tuples containing field name and sort direction 
                  (1 for ascending, -1 for descending).

        Returns:
            List of CategoryDiscountMasterDocument objects.
        """
        return await self.category_discount_master_repo.get_category_discount_by_filter_async({}, limit, page, sort)

    async def get_category_discount_paginated_async(self, limit: int, page: int, sort: list[tuple[str, int]]):
        """
        Retrieve all categories within the tenant with pagination metadata.

        Args:
            limit: Maximum number of records to return
            page: Page number for pagination
            sort: List of tuples containing field name and sort direction (1 for ascending, -1 for descending)

        Returns:
            PaginatedResult containing CategoryDiscountMasterDocument objects and metadata
        """
        return await self.category_discount_master_repo.get_category_discount_by_filter_paginated_async({}, limit, page, sort)

    async def update_category_discount_async(self, category_code: str, update_data: dict) -> CategoryDiscountMasterDocument:
        """
        Update an existing category discount with new values.

        Args:
            category_code: Unique identifier for the category to update.
            update_data: Dictionary containing the fields to update and their new values.

        Returns:
            Updated CategoryDiscountMasterDocument.

        Raises:
            DocumentNotFoundException: If no category discount with the given code exists.
        """

        # check if category exists
        # Currently only category_code is used. In full implementation, store_code should also be considered.
        category = await self.category_discount_master_repo.get_category_discount_by_code_async(category_code)
        if category is None:
            message = f"category with code {category_code} not found"
            raise DocumentNotFoundException(message, logger)

        # update category discount
        return await self.category_discount_master_repo.update_category_discount_async(category_code, update_data)
    
    async def get_category_discount_detail_by_code_async(self, category_code: str) -> CategoryDiscountDetailDocument:
        """
        Retrieve detailed discount information for a category.

        This method combines category-level discount master data with additional 
        discount store information to produce a detailed document.

        Args:
            category_code: Unique identifier for the category.

        Returns:
            CategoryDiscountDetailDocument containing both category-level and discount store data.

        Raises:
            DocumentNotFoundException: 
                - If no category discount master with the given code exists.
                - If the associated discount store record cannot be found.
        """
        logger.debug(f"get_category_discount_detail_by_code_async request received for category_code: {category_code}")

        category_discount_detail_doc = CategoryDiscountDetailDocument()
        
        # Currently only category_code is used. In full implementation, store_code should also be considered.
        category_discount_master_doc = await self.category_discount_master_repo.get_category_discount_by_code_async(category_code)
        if category_discount_master_doc is None:
            message = f"category discount master with code {category_code} not found"
            # raise DocumentNotFoundException(message, logger) 
            logger.info(message)
            return category_discount_detail_doc   
        else:
            logger.debug(f"category_code: {category_code}")
            category_discount_detail_doc.tenant_id = category_discount_master_doc.tenant_id
            category_discount_detail_doc.category_code = category_discount_master_doc.category_code
            category_discount_detail_doc.store_code = category_discount_master_doc.store_code
            category_discount_detail_doc.discount_code = category_discount_master_doc.discount_code
            category_discount_detail_doc.description = category_discount_master_doc.description
            #category_discount_detail_doc.description_short = category_discount_master_doc.description_short  Reserved field for demo purposes, currently not in use.

        discount_master = await self.discount_store_master_repo.get_discount_store_by_code_async(category_discount_master_doc.discount_code)
        if discount_master is None:
            message = f"discount store with code {category_discount_master_doc.discount_code} not found"
            raise DocumentNotFoundException(message, logger)
        else:
            category_discount_detail_doc.discount_value = discount_master.discount_value
        
        return category_discount_detail_doc
    
    async def delete_category_discount_async(self, category_code: str) -> None:
        """
        Delete a category discount from the database.

        Args:
            category_code: Unique identifier for the category to delete

        Raises:
            DocumentNotFoundException: If no category with the given code exists
        """
        # check if category discount  exists
        category = await self.category_discount_master_repo.get_category_discount_by_code_async(category_code)
        if category is None:
            message = f"category with code {category_code} not found"
            raise DocumentNotFoundException(message, logger)

        # delete category discount
        return await self.category_discount_master_repo.delete_category_discount_async(category_code)
