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
    CategoryDiscountMasterCreateRequest,
    CategoryDiscountMasterUpdateRequest,
    CategoryDiscountMasterResponse,
    CategoryDiscountMasterDeleteResponse,
    CategoryDiscountDetailResponse,

)
from app.api.v1.schemas_transformer import SchemasTransformerV1
from app.dependencies.get_master_services import get_category_discount_master_service_async
from app.dependencies.common import parse_sort

# Create a router instance for category discount master endpoints
router = APIRouter()

# Get a logger instance for this module
logger = getLogger(__name__)


@router.post(
    "/tenants/{tenant_id}/category_discounts",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[CategoryDiscountMasterResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: StatusCodes.get(status.HTTP_400_BAD_REQUEST),
        status.HTTP_401_UNAUTHORIZED: StatusCodes.get(status.HTTP_401_UNAUTHORIZED),
        status.HTTP_422_UNPROCESSABLE_ENTITY: StatusCodes.get(status.HTTP_422_UNPROCESSABLE_ENTITY),
        status.HTTP_500_INTERNAL_SERVER_ERROR: StatusCodes.get(status.HTTP_500_INTERNAL_SERVER_ERROR),
    },
)
async def create_category_discount(
    category: CategoryDiscountMasterCreateRequest,
    tenant_id: str = Path(...),
    tenant_id_with_security: str = Depends(get_tenant_id_with_security_by_query_optional),
):
    """
    Create a new category discount record.

    This endpoint allows creating a new discount for a specific store and category
    with its discount code, store code, value, and description. Category discounts
    are used to apply discounts to products within a specific category in the POS system.

    Authentication is required via token or API key. The tenant ID in the path must match
    the one in the security credentials.
    """
    logger.info(f"create_category_discount: category->{category}, tenant_id->{tenant_id}")
    verify_tenant_id(tenant_id, tenant_id_with_security, logger)
    service = await get_category_discount_master_service_async(tenant_id)
    
    try:
        new_category_discount = await service.create_category_discount_async(
            category_code=category.category_code,
            store_code=category.store_code,
            discount_code=category.discount_code,
            description=category.description,
        )
        tansformer = SchemasTransformerV1()
        return_category_discount = tansformer.transform_category_discount_master(new_category_discount)
    except Exception as e:
        logger.error(f"Error creating category discount: {e}")
        raise e

    response = ApiResponse(
        success=True,
        code=status.HTTP_201_CREATED,
        message=f"Category discount {category.category_code,category.discount_code} created successfully",
        data=return_category_discount.model_dump(),
        operation=f"{inspect.currentframe().f_code.co_name}",
    )
    return response


@router.get(
    "/tenants/{tenant_id}/category_discounts",
    response_model=ApiResponse[List[CategoryDiscountMasterResponse]],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: StatusCodes.get(status.HTTP_400_BAD_REQUEST),
        status.HTTP_401_UNAUTHORIZED: StatusCodes.get(status.HTTP_401_UNAUTHORIZED),
        status.HTTP_422_UNPROCESSABLE_ENTITY: StatusCodes.get(status.HTTP_422_UNPROCESSABLE_ENTITY),
        status.HTTP_500_INTERNAL_SERVER_ERROR: StatusCodes.get(status.HTTP_500_INTERNAL_SERVER_ERROR),
    },
)
async def get_category_discounts(
    tenant_id: str = Path(...),
    limit: int = Query(100),
    page: int = Query(1),
    sort: list[tuple[str, int]] = Depends(parse_sort),
    tenant_id_with_security: str = Depends(get_tenant_id_with_security_by_query_optional),
):
    """
    Retrieve all category discounts for a tenant with pagination and sorting.

    This endpoint returns a paginated list of all category discounts for the specified tenant.
    It can be used to manage discounts or display them in the POS system.

    Authentication is required via token or API key. The tenant ID in the path must match
    the one in the security credentials.

    Args:
        tenant_id: The tenant identifier from the path
        limit: Maximum number of categories to return (default: 100)
        page: Page number for pagination (default: 1)
        sort: Sorting criteria (default: category_code ascending)
        tenant_id_with_security: The tenant ID from security credentials

    Returns:
        ApiResponse[List[CategoryDiscountMasterResponse]]: Standard API response with a list of category data

    Raises:
        RepositoryException: If there's an error during database operations
    """
    logger.info(f"get_category_discounts: tenant_id->{tenant_id}")
    verify_tenant_id(tenant_id, tenant_id_with_security, logger)
    service = await get_category_discount_master_service_async(tenant_id)
    try:
        paginated_result = await service.get_category_discount_paginated_async(limit, page, sort)
        transformer = SchemasTransformerV1()
        return_categories = [transformer.transform_category_discount_master(category) for category in paginated_result.data]
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise e

    response = ApiResponse(
        success=True,
        code=status.HTTP_200_OK,
        message=f"Categories found successfully for tenant_id: {tenant_id}",
        data=[category.model_dump() for category in return_categories],
        metadata=paginated_result.metadata.model_dump(),
        operation=f"{inspect.currentframe().f_code.co_name}",
    )
    return response


@router.get(
    "/tenants/{tenant_id}/category_discounts/{category_code}",
    response_model=ApiResponse[CategoryDiscountMasterResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: StatusCodes.get(status.HTTP_400_BAD_REQUEST),
        status.HTTP_401_UNAUTHORIZED: StatusCodes.get(status.HTTP_401_UNAUTHORIZED),
        status.HTTP_404_NOT_FOUND: StatusCodes.get(status.HTTP_404_NOT_FOUND),
        status.HTTP_422_UNPROCESSABLE_ENTITY: StatusCodes.get(status.HTTP_422_UNPROCESSABLE_ENTITY),
        status.HTTP_500_INTERNAL_SERVER_ERROR: StatusCodes.get(status.HTTP_500_INTERNAL_SERVER_ERROR),
    },
)
async def get_category_discount(
    category_code: str,
    tenant_id: str = Path(...),
    tenant_id_with_security: str = Depends(get_tenant_id_with_security_by_query_optional),
):
    """
    Retrieve a specific category discount by its code.

    This endpoint retrieves the details of a category discount identified by its unique code,
    including its store, discount value, and description.

    Args:
        category_code: The unique code of the category to retrieve
        tenant_id: The tenant identifier from the path
        tenant_id_with_security: The tenant ID from security credentials

    Returns:
        ApiResponse[CategoryDiscountMasterResponse]: Standard API response with the category data

    Raises:
        DocumentNotFoundException: If the category with the given code is not found
        RepositoryException: If there's an error during database operations
    """
    logger.info(f"get_category: category_code->{category_code}, tenant_id->{tenant_id}")
    verify_tenant_id(tenant_id, tenant_id_with_security, logger)
    service = await get_category_discount_master_service_async(tenant_id)
    try:
        new_category_discount = await service.get_category_discount_by_code_async(category_code)
        if new_category_discount is None:
            message = f"Category {category_code} not found, tenant_id: {tenant_id}"
            raise DocumentNotFoundException(message, logger)
        transformer = SchemasTransformerV1()
        return_category_discount = transformer.transform_category_discount_master(new_category_discount)
    except Exception as e:
        logger.error(f"Error getting category: {e}")
        raise e

    response = ApiResponse(
        success=True,
        code=status.HTTP_200_OK,
        message=f"Category {category_code} found successfully for tenant_id: {tenant_id}",
        data=return_category_discount.model_dump(),
        operation=f"{inspect.currentframe().f_code.co_name}",
    )
    return response

@router.get(
    "/tenants/{tenant_id}/category_discounts/{category_code}/detail",
    response_model=ApiResponse[CategoryDiscountDetailResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: StatusCodes.get(status.HTTP_400_BAD_REQUEST),
        status.HTTP_401_UNAUTHORIZED: StatusCodes.get(status.HTTP_401_UNAUTHORIZED),
        status.HTTP_404_NOT_FOUND: StatusCodes.get(status.HTTP_404_NOT_FOUND),
        status.HTTP_422_UNPROCESSABLE_ENTITY: StatusCodes.get(status.HTTP_422_UNPROCESSABLE_ENTITY),
        status.HTTP_500_INTERNAL_SERVER_ERROR: StatusCodes.get(status.HTTP_500_INTERNAL_SERVER_ERROR),
    },
)
async def get_category_discount_detail(
    category_code: str,
    tenant_id: str = Path(...),
    tenant_id_with_security: str = Depends(get_tenant_id_with_security_by_query_optional),
):
    """
    """
    logger.info(f"get_category: category_code->{category_code}, tenant_id->{tenant_id}")
    verify_tenant_id(tenant_id, tenant_id_with_security, logger)
    service = await get_category_discount_master_service_async(tenant_id)
    try:
        category_discount_detail = await service.get_category_discount_detail_by_code_async(category_code)
        # if category_discount_detail is None:
            # logger.info(f"Category {category_code} not found, tenant_id: {tenant_id}")
            # raise DocumentNotFoundException(message, logger)
        transformer = SchemasTransformerV1()
        # return_category_discount_detail = transformer.transform_category_discount_detail(category_discount_detail)
        return_category_discount_detail = (
            transformer.transform_category_discount_detail(category_discount_detail)
            if category_discount_detail else None
        )
    except Exception as e:
        logger.error(f"Error getting category: {e}")
        raise e
    
    if return_category_discount_detail:
        message = f"Category {category_code} found successfully for tenant_id: {tenant_id}"
        data = return_category_discount_detail.model_dump()
    else:
        message = f"Category {category_code} not found for tenant_id: {tenant_id}"
        data = None

    response = ApiResponse(
        success=True,
        code=status.HTTP_200_OK,
        message=message,
        data=data,
        operation=f"{inspect.currentframe().f_code.co_name}",
    )
    return response


@router.put(
    "/tenants/{tenant_id}/category_discounts/{category_code}",
    response_model=ApiResponse[CategoryDiscountMasterResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: StatusCodes.get(status.HTTP_400_BAD_REQUEST),
        status.HTTP_401_UNAUTHORIZED: StatusCodes.get(status.HTTP_401_UNAUTHORIZED),
        status.HTTP_404_NOT_FOUND: StatusCodes.get(status.HTTP_404_NOT_FOUND),
        status.HTTP_422_UNPROCESSABLE_ENTITY: StatusCodes.get(status.HTTP_422_UNPROCESSABLE_ENTITY),
        status.HTTP_500_INTERNAL_SERVER_ERROR: StatusCodes.get(status.HTTP_500_INTERNAL_SERVER_ERROR),
    },
)
async def update_category_discount(
    category_code: str,
    category: CategoryDiscountMasterUpdateRequest,
    tenant_id: str = Path(...),
    tenant_id_with_security: str = Depends(get_tenant_id_with_security_by_query_optional),
):
    """
    Update an existing category discount.

    This endpoint allows updating the details of an existing category discount identified
    by its discount code. Fields such as discount value, store, and description can be modified.

    The discount_code itself cannot be changed, as it serves as a unique identifier.
    Updating a discount will affect all transactions using this discount.

    Args:
        category_code: The unique code of the category to update
        category: The updated category details
        tenant_id: The tenant identifier from the path
        tenant_id_with_security: The tenant ID from security credentials

    Returns:
        ApiResponse[CategoryDiscountMasterResponse]: Standard API response with the updated category data

    Raises:
        DocumentNotFoundException: If the category with the given code is not found
        InvalidRequestDataException: If the request data is invalid
        RepositoryException: If there's an error during database operations
    """
    logger.info(f"update_category_discount: category->{category}, tenant_id->{tenant_id}")
    verify_tenant_id(tenant_id, tenant_id_with_security, logger)
    service = await get_category_discount_master_service_async(tenant_id)
    try:
        updated_category_discount = await service.update_category_discount_async(
            category_code=category_code, update_data=category.model_dump()
        )
        if updated_category_discount is None:
            message = f"Category {category_code} not found, tenant_id: {tenant_id}"
            raise DocumentNotFoundException(message, logger)
        transformer = SchemasTransformerV1()
        return_category = transformer.transform_category_discount_master(updated_category_discount)
    except Exception as e:
        logger.error(f"Error updating category: {e}")
        raise e

    response = ApiResponse(
        success=True,
        code=status.HTTP_200_OK,
        message=f"Category {category_code} updated successfully for tenant_id: {tenant_id}",
        data=return_category.model_dump(),
        operation=f"{inspect.currentframe().f_code.co_name}",
    )
    return response


@router.delete(
    "/tenants/{tenant_id}/category_discounts/{category_code}",
    response_model=ApiResponse[CategoryDiscountMasterDeleteResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: StatusCodes.get(status.HTTP_400_BAD_REQUEST),
        status.HTTP_401_UNAUTHORIZED: StatusCodes.get(status.HTTP_401_UNAUTHORIZED),
        status.HTTP_404_NOT_FOUND: StatusCodes.get(status.HTTP_404_NOT_FOUND),
        status.HTTP_422_UNPROCESSABLE_ENTITY: StatusCodes.get(status.HTTP_422_UNPROCESSABLE_ENTITY),
        status.HTTP_500_INTERNAL_SERVER_ERROR: StatusCodes.get(status.HTTP_500_INTERNAL_SERVER_ERROR),
    },
)
async def delete_category_discount(
    category_code: str,
    tenant_id: str = Path(...),
    tenant_id_with_security: str = Depends(get_tenant_id_with_security_by_query_optional),
):
    """
    Delete a category discount.

    This endpoint removes a category discount from the system.
    Caution should be exercised, as deleting a discount that is applied to active
    transactions or promotions may cause inconsistencies.

    Authentication is required via token or API key. The tenant ID in the path must match
    the one in the security credentials.

    Args:
        category_code: The unique code of the category to delete
        tenant_id: The tenant identifier from the path
        tenant_id_with_security: The tenant ID from security credentials

    Returns:
        ApiResponse[CategoryDiscountMasterDeleteResponse]: Standard API response with deletion confirmation

    Raises:
        DocumentNotFoundException: If the category with the given code is not found
        RepositoryException: If there's an error during database operations
    """
    logger.info(f"delete_category_discount: category_code->{category_code}, tenant_id->{tenant_id}")
    verify_tenant_id(tenant_id, tenant_id_with_security, logger)
    service = await get_category_discount_master_service_async(tenant_id)
    # Check if the category discount exists before attempting to delete
    existing_category_discount = await service.get_category_discount_by_code_async(category_code)
    if existing_category_discount is None:
        message = f"Category {category_code} not found, tenant_id: {tenant_id}"
        raise DocumentNotFoundException(message, logger)
    try:
        await service.delete_category_discount_async(category_code)
    except Exception as e:
        logger.error(f"Error deleting category: {e} for tenant_id: {tenant_id}")
        raise e

    response = ApiResponse(
        success=True,
        code=status.HTTP_200_OK,
        message=f"Category {category_code} deleted successfully for tenant_id: {tenant_id}",
        data=CategoryDiscountMasterDeleteResponse(
            category_code=existing_category_discount.category_code,
            store_code= existing_category_discount.store_code,
            discount_code=existing_category_discount.discount_code).model_dump(),
        operation=f"{inspect.currentframe().f_code.co_name}",
    )
    return response
