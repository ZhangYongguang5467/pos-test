# Copyright 2025 masa@kugel  # # Licensed under the Apache License, Version 2.0 (the "License");  # you may not use this file except in compliance with the License.  # You may obtain a copy of the License at  # #     http://www.apache.org/licenses/LICENSE-2.0  # # Unless required by applicable law or agreed to in writing, software  # distributed under the License is distributed on an "AS IS" BASIS,  # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  # See the License for the specific language governing permissions and  # limitations under the License.
from fastapi import APIRouter, status, HTTPException, Depends, Path, Query
from logging import getLogger
from typing import List
import inspect

from kugel_common.database import database as db_helper
from kugel_common.status_codes import StatusCodes
from kugel_common.security import get_tenant_id_with_security_by_query_optional, verify_tenant_id
from kugel_common.schemas.api_response import ApiResponse
from kugel_common.exceptions import (
    InvalidRequestDataException,
    DocumentAlreadyExistsException,
    DocumentNotFoundException,
    RepositoryException,
)

from app.config.settings import settings
from app.api.v1.schemas import (
    DiscountStoreMasterCreateRequest,
    DiscountStoreMasterUpdateRequest,
    DiscountStoreMasterResponse,
    DiscountStoreMasterDeleteResponse,

)
from app.api.v1.schemas_transformer import SchemasTransformerV1
from app.dependencies.get_master_services import get_discount_store_master_service_async
from app.dependencies.common import parse_sort

# Create a router instance for discount master endpoints
router = APIRouter()

# Get a logger instance for this module
logger = getLogger(__name__)


@router.post(
    "/tenants/{tenant_id}/discount",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[DiscountStoreMasterResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: StatusCodes.get(status.HTTP_400_BAD_REQUEST),
        status.HTTP_401_UNAUTHORIZED: StatusCodes.get(status.HTTP_401_UNAUTHORIZED),
        status.HTTP_422_UNPROCESSABLE_ENTITY: StatusCodes.get(status.HTTP_422_UNPROCESSABLE_ENTITY),
        status.HTTP_500_INTERNAL_SERVER_ERROR: StatusCodes.get(status.HTTP_500_INTERNAL_SERVER_ERROR),
    },
)
async def create_discount_store(
    discount: DiscountStoreMasterCreateRequest,
    tenant_id: str = Path(...),
    tenant_id_with_security: str = Depends(get_tenant_id_with_security_by_query_optional),
):
    """
    Create a new discount for a store.

    This endpoint allows creating a new store-level discount with its discount code,
    store code, discount value, and description. Store discounts are used to apply
    specific discounts to products in a particular store.

    Authentication is required via token or API key. The tenant ID in the path must match
    the one in the security credentials.

    Args:
        discount: The discount details to create
        tenant_id: The tenant identifier from the path
        tenant_id_with_security: The tenant ID from security credentials

    Returns:
        ApiResponse[DiscountStoreMasterResponse]: Standard API response with the created discount data

    Raises:
        DocumentAlreadyExistsException: If a discount with the same code already exists
        InvalidRequestDataException: If the request data is invalid
        RepositoryException: If there's an error during database operations
        """
    logger.info(f"create_discount_store: discount->{discount}, tenant_id->{tenant_id}")
    verify_tenant_id(tenant_id, tenant_id_with_security, logger)
    service = await get_discount_store_master_service_async(tenant_id)
    
    try:
        new_discount = await service.create_discount_store_async(
            discount_code=discount.discount_code,
            store_code=discount.store_code,
            discount_value=discount.discount_value,
            description=discount.description,
        )
        tansformer = SchemasTransformerV1()
        return_category_discount = tansformer.transform_discount_store_master(new_discount)
    except Exception as e:
        logger.error(f"Error creating discount: {e}")
        raise e

    response = ApiResponse(
        success=True,
        code=status.HTTP_201_CREATED,
        message=f"Category discount {discount.discount_code,discount.discount_value} created successfully",
        data=return_category_discount.model_dump(),
        operation=f"{inspect.currentframe().f_code.co_name}",
    )
    return response


@router.get(
    "/tenants/{tenant_id}/discount",
    response_model=ApiResponse[List[DiscountStoreMasterResponse]],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: StatusCodes.get(status.HTTP_400_BAD_REQUEST),
        status.HTTP_401_UNAUTHORIZED: StatusCodes.get(status.HTTP_401_UNAUTHORIZED),
        status.HTTP_422_UNPROCESSABLE_ENTITY: StatusCodes.get(status.HTTP_422_UNPROCESSABLE_ENTITY),
        status.HTTP_500_INTERNAL_SERVER_ERROR: StatusCodes.get(status.HTTP_500_INTERNAL_SERVER_ERROR),
    },
)
async def get_discounts(
    tenant_id: str = Path(...),
    limit: int = Query(100),
    page: int = Query(1),
    sort: list[tuple[str, int]] = Depends(parse_sort),
    tenant_id_with_security: str = Depends(get_tenant_id_with_security_by_query_optional),
):
    """
    Retrieve all store discounts for a tenant with pagination and sorting.

    This endpoint returns a paginated list of all store-level discounts for the specified tenant.
    The results can be sorted and paginated as needed. It is typically used to manage discounts
    or display them in the POS system.

    Authentication is required via token or API key. The tenant ID in the path must match
    the one in the security credentials.

    Args:
        tenant_id: The tenant identifier from the path
        limit: Maximum number of discounts to return (default: 100)
        page: Page number for pagination (default: 1)
        sort: Sorting criteria (default: discount_code ascending)
        tenant_id_with_security: The tenant ID from security credentials

    Returns:
        ApiResponse[List[DiscountStoreMasterResponse]]: Standard API response with a list of discount data

    Raises:
        RepositoryException: If there's an error during database operations
    """
    logger.info(f"get_discounts: tenant_id->{tenant_id}")
    verify_tenant_id(tenant_id, tenant_id_with_security, logger)
    service = await get_discount_store_master_service_async(tenant_id)
    try:
        paginated_result = await service.get_discount_store_paginated_async(limit, page, sort)
        transformer = SchemasTransformerV1()
        return_discounts = [transformer.transform_discount_store_master(discount) for discount in paginated_result.data]
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise e

    response = ApiResponse(
        success=True,
        code=status.HTTP_200_OK,
        message=f"Categories found successfully for tenant_id: {tenant_id}",
        data=[discount.model_dump() for discount in return_discounts],
        metadata=paginated_result.metadata.model_dump(),
        operation=f"{inspect.currentframe().f_code.co_name}",
    )
    return response


@router.get(
    "/tenants/{tenant_id}/discount/{discount_code}",
    response_model=ApiResponse[DiscountStoreMasterResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: StatusCodes.get(status.HTTP_400_BAD_REQUEST),
        status.HTTP_401_UNAUTHORIZED: StatusCodes.get(status.HTTP_401_UNAUTHORIZED),
        status.HTTP_404_NOT_FOUND: StatusCodes.get(status.HTTP_404_NOT_FOUND),
        status.HTTP_422_UNPROCESSABLE_ENTITY: StatusCodes.get(status.HTTP_422_UNPROCESSABLE_ENTITY),
        status.HTTP_500_INTERNAL_SERVER_ERROR: StatusCodes.get(status.HTTP_500_INTERNAL_SERVER_ERROR),
    },
)
async def get_discount(
    discount_code: str,
    tenant_id: str = Path(...),
    tenant_id_with_security: str = Depends(get_tenant_id_with_security_by_query_optional),
):
    """
    Retrieve a specific store discount by its discount code.

    This endpoint retrieves the details of a store discount identified by its unique discount code,
    including store code, discount value, and description.

    Authentication is required via token or API key. The tenant ID in the path must match
    the one in the security credentials.

    Args:
        discount_code: The unique code of the discount to retrieve
        tenant_id: The tenant identifier from the path
        tenant_id_with_security: The tenant ID from security credentials

    Returns:
        ApiResponse[DiscountStoreMasterResponse]: Standard API response with the discount data

    Raises:
        DocumentNotFoundException: If the discount with the given code is not found
        RepositoryException: If there's an error during database operations
    """
    logger.info(f"get_category: category_code->{discount_code}, tenant_id->{tenant_id}")
    verify_tenant_id(tenant_id, tenant_id_with_security, logger)
    service = await get_discount_store_master_service_async(tenant_id)
    try:
        new_discount = await service.get_discount_store_by_code_async(discount_code)
        if new_discount is None:
            message = f"Discount {discount_code} not found, tenant_id: {tenant_id}"
            raise DocumentNotFoundException(message, logger)
        transformer = SchemasTransformerV1()
        return_discount = transformer.transform_discount_store_master(new_discount)
    except Exception as e:
        logger.error(f"Error getting category: {e}")
        raise e

    response = ApiResponse(
        success=True,
        code=status.HTTP_200_OK,
        message=f"Discount {discount_code} found successfully for tenant_id: {tenant_id}",
        data=return_discount.model_dump(),
        operation=f"{inspect.currentframe().f_code.co_name}",
    )
    return response


@router.put(
    "/tenants/{tenant_id}/discount/{discount_code}",
    response_model=ApiResponse[DiscountStoreMasterResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: StatusCodes.get(status.HTTP_400_BAD_REQUEST),
        status.HTTP_401_UNAUTHORIZED: StatusCodes.get(status.HTTP_401_UNAUTHORIZED),
        status.HTTP_404_NOT_FOUND: StatusCodes.get(status.HTTP_404_NOT_FOUND),
        status.HTTP_422_UNPROCESSABLE_ENTITY: StatusCodes.get(status.HTTP_422_UNPROCESSABLE_ENTITY),
        status.HTTP_500_INTERNAL_SERVER_ERROR: StatusCodes.get(status.HTTP_500_INTERNAL_SERVER_ERROR),
    },
)
async def update_discount(
    discount_code: str,
    discount: DiscountStoreMasterUpdateRequest,
    tenant_id: str = Path(...),
    tenant_id_with_security: str = Depends(get_tenant_id_with_security_by_query_optional),
):
    """
    Update an existing product category.

    This endpoint allows updating the details of an existing category identified
    by its code. It can be used to modify the description, short description, or tax code.

    The category_code itself cannot be changed, as it serves as a unique identifier.
    Updating a category will affect all products assigned to this category.

    Authentication is required via token or API key. The tenant ID in the path must match
    the one in the security credentials.

    Args:
        discount_code: The unique code of the category to update
        category: The updated category details
        tenant_id: The tenant identifier from the path
        tenant_id_with_security: The tenant ID from security credentials

    Returns:
        ApiResponse[CategoryMasterResponse]: Standard API response with the updated category data

    Raises:
        DocumentNotFoundException: If the category with the given code is not found
        InvalidRequestDataException: If the request data is invalid
        RepositoryException: If there's an error during database operations
    """
    logger.info(f"update_discount: discount->{discount}, tenant_id->{tenant_id}")
    verify_tenant_id(tenant_id, tenant_id_with_security, logger)
    service = await get_discount_store_master_service_async(tenant_id)
    try:
        updated_discount = await service.update_discount_store_async(
            discount_code=discount_code, update_data=discount.model_dump()
        )
        if updated_discount is None:
            message = f"Discount {discount_code} not found, tenant_id: {tenant_id}"
            raise DocumentNotFoundException(message, logger)
        transformer = SchemasTransformerV1()
        return_discount = transformer.transform_discount_store_master(updated_discount)
    except Exception as e:
        logger.error(f"Error updating category: {e}")
        raise e

    response = ApiResponse(
        success=True,
        code=status.HTTP_200_OK,
        message=f"Discount {discount_code} updated successfully for tenant_id: {tenant_id}",
        data=return_discount.model_dump(),
        operation=f"{inspect.currentframe().f_code.co_name}",
    )
    return response


@router.delete(
    "/tenants/{tenant_id}/discount/{discount_code}",
    response_model=ApiResponse[DiscountStoreMasterDeleteResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: StatusCodes.get(status.HTTP_400_BAD_REQUEST),
        status.HTTP_401_UNAUTHORIZED: StatusCodes.get(status.HTTP_401_UNAUTHORIZED),
        status.HTTP_404_NOT_FOUND: StatusCodes.get(status.HTTP_404_NOT_FOUND),
        status.HTTP_422_UNPROCESSABLE_ENTITY: StatusCodes.get(status.HTTP_422_UNPROCESSABLE_ENTITY),
        status.HTTP_500_INTERNAL_SERVER_ERROR: StatusCodes.get(status.HTTP_500_INTERNAL_SERVER_ERROR),
    },
)
async def delete_discount(
    discount_code: str,
    tenant_id: str = Path(...),
    tenant_id_with_security: str = Depends(get_tenant_id_with_security_by_query_optional),
):
    """
    Delete a store discount.

    This endpoint removes a store discount from the system.
    Caution should be exercised, as deleting a discount that is currently applied
    to active transactions or promotions may cause inconsistencies.

    Authentication is required via token or API key. The tenant ID in the path must match
    the one in the security credentials.

    Args:
        discount_code: The unique code of the discount to delete
        tenant_id: The tenant identifier from the path
        tenant_id_with_security: The tenant ID from security credentials

    Returns:
        ApiResponse[DiscountStoreMasterDeleteResponse]: Standard API response with deletion confirmation

    Raises:
        DocumentNotFoundException: If the discount with the given code is not found
        RepositoryException: If there's an error during database operations
    """
    logger.info(f"delete_discount: category_code->{discount_code}, tenant_id->{tenant_id}")
    verify_tenant_id(tenant_id, tenant_id_with_security, logger)
    service = await get_discount_store_master_service_async(tenant_id)

    # check if discount exists
    # Currently only discount_code is used. In full implementation, store_code should also be considered
    discount = await service.get_discount_store_by_code_async(discount_code)
    if discount is None:
        message = f"discount_code with code {discount_code} not found"
        raise DocumentNotFoundException(message, logger)
    try:
        await service.delete_discount_store_async(discount_code)
    except Exception as e:
        logger.error(f"Error deleting discount: {e} for tenant_id: {tenant_id}")
        raise e

    response = ApiResponse(
        success=True,
        code=status.HTTP_200_OK,
        message=f"discount {discount_code} deleted successfully for tenant_id: {tenant_id}",
        data=DiscountStoreMasterDeleteResponse(
            discount_code=discount.discount_code,
            store_code=discount.store_code,
            discount_value=discount.discount_value,
            ).model_dump(),
        operation=f"{inspect.currentframe().f_code.co_name}",
    )
    return response
