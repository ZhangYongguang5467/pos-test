# Copyright 2025 masa@kugel  # # Licensed under the Apache License, Version 2.0 (the "License");  # you may not use this file except in compliance with the License.  # You may obtain a copy of the License at  # #     http://www.apache.org/licenses/LICENSE-2.0  # # Unless required by applicable law or agreed to in writing, software  # distributed under the License is distributed on an "AS IS" BASIS,  # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  # See the License for the specific language governing permissions and  # limitations under the License.
from typing import Optional
from app.models.documents.abstract_document import AbstractDocument


class DiscountStoreMasterDocument(AbstractDocument):
    """
    Document class representing store-specific discount information for a product/item category.

    This class defines the structure for category-level discount data that is applied
    to items in specific stores. It supports multi-tenancy and allows both full and
    abbreviated descriptions for reporting and display purposes. Discounts can be
    referenced by code and can include a value or percentage to define the promotion.
    """

    tenant_id: Optional[str] = None  # Unique identifier for the tenant (multi-tenancy support)
    store_code: Optional[str] = None  # Identifier for the specific store
    discount_code: Optional[str] = None  # Reference to the discount code applied to items in this category
    discount_value: Optional[float] = None  # Value or percentage of the discount; defines how much the discount reduces the price
    description: Optional[str] = None  # Full description of the discount
