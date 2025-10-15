# Copyright 2025 masa@kugel  # # Licensed under the Apache License, Version 2.0 (the "License");  # you may not use this file except in compliance with the License.  # You may obtain a copy of the License at  # #     http://www.apache.org/licenses/LICENSE-2.0  # # Unless required by applicable law or agreed to in writing, software  # distributed under the License is distributed on an "AS IS" BASIS,  # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  # See the License for the specific language governing permissions and  # limitations under the License.
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

from kugel_common.models.documents.abstract_document import AbstractDocument
from kugel_common.utils.misc import to_lower_camel


class CategoryDiscountDetailsDocument(AbstractDocument):
    """
    Document model representing category discount data.

    Fields `store_code` and `discount_code` are identifiers and should
    generally come from the URL / Path rather than body payload when updating.
    This prevents inconsistencies between body and path parameters.

    """
    tenant_id: Optional[str] = None  # Unique identifier for the tenant (multi-tenancy support)
    category_code: Optional[str] = None  # Unique code identifying this category within a tenant
    store_code: Optional[str] = None  # Identifier for the specific store
    discount_code: Optional[str] = None  # Reference to the discount code applied to items in this category
    description: Optional[str] = None  # Full description of the discount
    description_short: Optional[str] = None  # Reserved field for demo purposes, currently not in use.
    discount_value: Optional[float] = None  # Value or percentage of the discount; defines how much the discount reduces the price

     # Configuration for Pydantic model to use camelCase field names in JSON
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_lower_camel)
