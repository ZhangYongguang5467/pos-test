# Copyright 2025 masa@kugel  # # Licensed under the Apache License, Version 2.0 (the "License");  # you may not use this file except in compliance with the License.  # You may obtain a copy of the License at  # #     http://www.apache.org/licenses/LICENSE-2.0  # # Unless required by applicable law or agreed to in writing, software  # distributed under the License is distributed on an "AS IS" BASIS,  # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  # See the License for the specific language governing permissions and  # limitations under the License.
from typing import Optional

from pydantic import field_validator
from app.models.documents.abstract_document import AbstractDocument
from app.models.documents.category_discount_master_document import CategoryDiscountMasterDocument


class CategoryDiscountDetailDocument(CategoryDiscountMasterDocument):
    """
    Document model for representing category-level discount details.

    This document extends the CategoryDiscountMasterDocument to provide more 
    specific discount information for product/item categories. It is typically 
    used in pricing and promotional workflows, ensuring that discounts can be 
    consistently applied and tracked across multiple tenants.

    Attributes:
        discount_code (Optional[str]): 
            A unique code that identifies the discount applied to this category.
            Useful for referencing and validating discount rules in transactions.
        
        discount_value (Optional[float]): 
            The discount amount or percentage to apply. This field defines the 
            reduction applied to item prices within the category.
            Example:
                - 0   → 0% (no discount)
                - 20  → 20% (0.20 multiplier)
                - 100 → 100% (free item)
    """

    discount_code: Optional[str] = None  # Unique code referencing the discount rule applied to this category
    discount_value: Optional[float] = None  # Discount rate stored as an float (0.00–100.00); convert to percentage when applied

    @field_validator("discount_value")
    @classmethod
    def validate_discount_value(cls, v: Optional[float]) -> Optional[float]:
        """Ensure discount_value is within 0.00–100.00 if provided."""
        if v is not None:
            if v < 0.0 or v > 100.0:
                raise ValueError("discount_value must be between 0.00 and 100.00")
        return v
