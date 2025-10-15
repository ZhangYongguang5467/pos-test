# Copyright 2025 masa@kugel  # # Licensed under the Apache License, Version 2.0 (the "License");  # you may not use this file except in compliance with the License.  # You may obtain a copy of the License at  # #     http://www.apache.org/licenses/LICENSE-2.0  # # Unless required by applicable law or agreed to in writing, software  # distributed under the License is distributed on an "AS IS" BASIS,  # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  # See the License for the specific language governing permissions and  # limitations under the License.
from typing import Optional
from app.models.documents.abstract_document import AbstractDocument


class CategoryDiscountMasterDocument(AbstractDocument):
    """
    Document model representing master-level discount information for a product/item category.

    This model defines the base structure of category-level discount data, typically used 
    to manage pricing or promotional rules across multiple tenants and stores. It supports 
    detailed and abbreviated descriptions to cover both reporting and UI display needs.
    """

    tenant_id: Optional[str] = None  # Unique identifier for the tenant (multi-tenancy support)
    category_code: Optional[str] = None  # Unique code identifying this category within a tenant
    store_code: Optional[str] = None  # Identifier for the specific store
    discount_code: Optional[str] = None  # Code referencing the discount rule for this category
    description: Optional[str] = None  # Full description of the discount
    description_short: Optional[str] = None  # Shortened description for display in limited space
