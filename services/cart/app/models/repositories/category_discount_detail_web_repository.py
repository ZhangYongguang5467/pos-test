# Copyright 2025 masa@kugel  # # Licensed under the Apache License, Version 2.0 (the "License");  # you may not use this file except in compliance with the License.  # You may obtain a copy of the License at  # #     http://www.apache.org/licenses/LICENSE-2.0  # # Unless required by applicable law or agreed to in writing, software  # distributed under the License is distributed on an "AS IS" BASIS,  # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  # See the License for the specific language governing permissions and  # limitations under the License.
from kugel_common.exceptions import RepositoryException, NotFoundException
from kugel_common.utils.http_client_helper import get_service_client
from kugel_common.models.documents.terminal_info_document import TerminalInfoDocument
from app.models.documents.category_discount_details_document import CategoryDiscountDetailsDocument
from app.config.settings import settings


from logging import getLogger

logger = getLogger(__name__)


class CategoryDiscountDetailWebRepository:
    """
    Repository class for accessing category discount details via the master data web API.

    Notes:
    - Fields like `store_code` and `discount_code` are unique identifiers and should
      generally be obtained from the URL/path parameters, not from the request body.
      This avoids inconsistencies when updating or querying data.
    - Other fields such as `description`, `description_short`, and `discount_value`
      are updatable and can be provided in request body payloads.
    - This repository supports caching of fetched documents to minimize redundant
      API calls and improve performance.
    - If a requested category discount is not found in cache, it will fetch from the
      master data API and append to the cache.

    Attributes:
        tenant_id: Tenant identifier (multi-tenancy support)
        store_code: Store identifier (unique per store)
        terminal_info: Terminal info document including API key
        category_code: Category code for which discounts are applied
        category_discount_detail_documents: Optional cache of CategoryDiscountDetailsDocument
        base_url: Base URL of master data service
    """

    def __init__(
        self,
        tenant_id: str,
        store_code: str,
        terminal_info: TerminalInfoDocument,
        category_code: str,
        category_discount_detail_documents: list[CategoryDiscountDetailsDocument] = None,
    ):
        """
        Initialize the repository with tenant, store, and terminal information.

        Args:
            tenant_id: Tenant identifier
            store_code: Store identifier
            terminal_info: Terminal information document containing API key
            category_code: Category code for which discounts are applied
            category_discount_detail_documents: Optional preloaded cache of category discount documents
        """
        self.tenant_id = tenant_id
        self.store_code = store_code
        self.terminal_info = terminal_info
        self.category_code = category_code
        self.category_discount_detail_documents = category_discount_detail_documents
        self.base_url = settings.BASE_URL_MASTER_DATA

    def set_category_discount_detail_documents(self, category_discount_detail_documents: list):
        """
        Set or replace the cached category discount documents.

        Args:
            category_discount_detail_documents: List of category discount documents to cache
        """
        self.category_discount_detail_documents = category_discount_detail_documents

    # get category discount detail
    async def get_category_discount_detail_by_code_async(self, category_code: str) -> CategoryDiscountDetailsDocument:
        """
        Retrieve a category discount detail by its code.

        First checks the cache. If the document is not cached, fetches it from
        the master data API and appends it to the cache.

        Args:
            category_code: Unique code of the category discount to retrieve

        Returns:
            CategoryDiscountDetailsDocument: The requested category discount detail

        Raises:
            NotFoundException: If the category discount detail is not found
            RepositoryException: If there is an error during the API request
        """
        if self.category_discount_detail_documents is None:
            self.category_discount_detail_documents = []

        # first check item_code exist in the list of item_master_documents
        # Currently only category_code is used. In full implementation, store_code should also be considered
        item = next((item for item in self.category_discount_detail_documents if item.category_code == category_code), None)
        if item is not None:
            logger.info(
                f"CategoryDiscountDetailRepository.get_item_by_code: item_code->{category_code} in the list of CategoryDiscountDetailDocument"
            )
            return item

        async with get_service_client("master-data") as client:
            headers = {"X-API-KEY": self.terminal_info.api_key}
            params = {"terminal_id": self.terminal_info.terminal_id}
            endpoint = f"/tenants/{self.tenant_id}/category_discounts/{category_code}/detail"

            try:
                response_data = await client.get(endpoint, params=params, headers=headers)
            except Exception as e:
                if hasattr(e, "status_code") and e.status_code == 404:
                    message = f"category discount detail not found for id {category_code}"
                    raise NotFoundException(
                        message=message,
                        collection_name="category discount detail web",
                        find_key=category_code,
                        logger=logger,
                        original_exception=e,
                    )
                else:
                    message = f"Request error for id {category_code}"
                    raise RepositoryException(
                        message=message, collection_name="category discount detail web", logger=logger, original_exception=e
                    )

            logger.debug(f"response: {response_data}")

            category_discount_detail = CategoryDiscountDetailsDocument(**response_data.get("data"))
            self.category_discount_detail_documents.append(category_discount_detail)
            return category_discount_detail
