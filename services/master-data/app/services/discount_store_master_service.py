# Copyright 2025 masa@kugel  # # Licensed under the Apache License, Version 2.0 (the "License");  # you may not use this file except in compliance with the License.  # You may obtain a copy of the License at  # #     http://www.apache.org/licenses/LICENSE-2.0  # # Unless required by applicable law or agreed to in writing, software  # distributed under the License is distributed on an "AS IS" BASIS,  # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  # See the License for the specific language governing permissions and  # limitations under the License.
from logging import getLogger
from typing import Any

from kugel_common.exceptions import DocumentNotFoundException, DocumentAlreadyExistsException
from app.models.documents.discount_store_master_document import DiscountStoreMasterDocument
from app.models.repositories.discount_store_master_repository import DiscountStoreMasterRepository
from app.models.repositories.category_master_repository import CategoryMasterRepository

logger = getLogger(__name__)


class DiscountStoreMasterService:
    """
    Service class for managing discount store master data operations.

    Provides business logic for creating, retrieving, updating, and deleting
    discount store records in the master data database.
    """

    def __init__(self, discount_store_master_repo: DiscountStoreMasterRepository):
        """
        Initialize the DiscountStoreMasterService with a repository.

        Args:
            discount_store_master_repo: Repository for discount store master data operations
        """
        self.discount_store_master_repo = discount_store_master_repo

    async def create_discount_store_async(
        self, discount_code: str,store_code:str,discount_value:str, description: str
    ) -> DiscountStoreMasterDocument:
        """
        Create a new discount store record.

        Args:
            discount_code: Unique identifier for the discount.
            store_code: Store identifier associated with this discount.
            discount_value: Value of the discount (e.g., percentage or fixed amount).
            description: Description of the discount.

        Returns:
            DiscountStoreMasterDocument: The newly created discount record.

        Raises:
            DocumentAlreadyExistsException: If a discount with the given code already exists.
        """

        # check if discount_code master exists
        # Currently only discount_code is used. In full implementation, store_code should also be considered.
        discount = await self.discount_store_master_repo.get_discount_store_by_code_async(discount_code)
        if discount is not None:
            message = f"discount with code {discount_code} already exists. tenant_id: {discount.tenant_id}"
            raise DocumentAlreadyExistsException(message, logger)   

        discount_store_doc = DiscountStoreMasterDocument()
        discount_store_doc.discount_code = discount_code
        discount_store_doc.store_code = store_code  
        discount_store_doc.discount_value = discount_value 
        discount_store_doc.description = description
        return await self.discount_store_master_repo.create_discount_store_async(discount_store_doc)

    async def get_discount_store_by_code_async(self, discount_code: str) -> DiscountStoreMasterDocument:
        """
        Retrieve a discount store record by its unique code.

        Args:
            discount_code: Unique identifier for the discount.

        Returns:
            DiscountStoreMasterDocument: The discount record with the specified code.

        Raises:
            DocumentNotFoundException: If no discount with the given code exists.
        """
        # Currently only discount_code is used. In full implementation, store_code should also be considered.
        discount = await self.discount_store_master_repo.get_discount_store_by_code_async(discount_code)
        if discount is None:
            message = f"discount with code {discount_code} not found"
            raise DocumentNotFoundException(message, logger)
        return discount 

    async def get_discount_store_async(self, limit: int, page: int, sort: list[tuple[str, int]]) -> list:
        """
        Retrieve discount store records with pagination and sorting.

        Args:
            limit: Maximum number of records to return.
            page: Page number for pagination.
            sort: List of tuples (field, direction), direction: 1=ascending, -1=descending.

        Returns:
            List[DiscountStoreMasterDocument] or PaginatedResult[DiscountStoreMasterDocument]
        """
        return await self.discount_store_master_repo.get_discount_store_by_filter_async({}, limit, page, sort)

    async def get_discount_store_paginated_async(self, limit: int, page: int, sort: list[tuple[str, int]]):
        """
        Retrieve discount store records with pagination and sorting.

        Args:
            limit: Maximum number of records to return.
            page: Page number for pagination.
            sort: List of tuples (field, direction), direction: 1=ascending, -1=descending.

        Returns:
            List[DiscountStoreMasterDocument] or PaginatedResult[DiscountStoreMasterDocument]
        """
        return await self.discount_store_master_repo.get_discount_store_by_filter_paginated_async({}, limit, page, sort)

    async def update_discount_store_async(self, discount_code: str, update_data: dict) -> DiscountStoreMasterDocument:
        """
        Update an existing discount store record.

        Args:
            discount_code: Unique identifier for the discount to update.
            update_data: Dictionary containing fields to update and their new values.

        Returns:
            DiscountStoreMasterDocument: Updated discount record.

        Raises:
            DocumentNotFoundException: If no discount with the given code exists.
        """

        # check if discount exists
        # Currently only discount_code is used. In full implementation, store_code should also be considered.
        discount = await self.discount_store_master_repo.get_discount_store_by_code_async(discount_code)
        if discount is None:
            message = f"discount with code {discount_code} not found"
            raise DocumentNotFoundException(message, logger)    

        # update discount
        return await self.discount_store_master_repo.update_discount_store_async(discount_code, update_data)

    async def delete_discount_store_async(self, discount_code: str) -> None:
        """
        Delete a discount store record from the database.

        Args:
            discount_code: Unique identifier for the discount to delete.

        Raises:
            DocumentNotFoundException: If no discount with the given code exists.
        """
        # check if discount exists
        # Currently only discount_code is used. In full implementation, store_code should also be considered.
        discount = await self.discount_store_master_repo.get_discount_store_by_code_async(discount_code)    
        if discount is None:
            message = f"discount_code with code {discount_code} not found"
            raise DocumentNotFoundException(message, logger)

        # delete discount
        return await self.discount_store_master_repo.delete_discount_store_async(discount_code)
