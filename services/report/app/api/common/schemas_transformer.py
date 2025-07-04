# Copyright 2025 masa@kugel  # # Licensed under the Apache License, Version 2.0 (the "License");  # you may not use this file except in compliance with the License.  # You may obtain a copy of the License at  # #     http://www.apache.org/licenses/LICENSE-2.0  # # Unless required by applicable law or agreed to in writing, software  # distributed under the License is distributed on an "AS IS" BASIS,  # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  # See the License for the specific language governing permissions and  # limitations under the License.
from logging import getLogger
from kugel_common.models.documents.base_tranlog import BaseTransaction
from app.api.common.schemas import *
from app.models.documents.sales_report_document import SalesReportDocument

logger = getLogger(__name__)


class SchemasTransformer:
    """
    Schema Transformer class for converting internal data models to API response schemas.

    This class handles the transformation of internal document models into standardized
    API response formats that follow the API contract. It ensures consistent data
    representation across the application's external interfaces.
    """

    def __init__(self):
        """Initialize the SchemasTransformer class."""
        pass

    def transform_tran_response(self, tran: BaseTransaction) -> BaseTranResponse:
        """
        Transform a base transaction document into a transaction response schema.

        This method converts internal transaction document models into the format
        expected by API consumers, including only the necessary identifying fields.

        Args:
            tran: The base transaction document to transform

        Returns:
            BaseTranResponse: API response schema with transaction details
        """
        return BaseTranResponse(
            tenant_id=tran.tenant_id,
            store_code=tran.store_code,
            terminal_no=tran.terminal_no,
            transaction_no=tran.transaction_no,
        )

    def transform_sales_report_response(self, report_doc: SalesReportDocument) -> BaseSalesReportResponse:
        """
        Transform a sales report document into a sales report response schema.

        This method handles the conversion of a complex sales report document into
        a standardized API response format, including all sales metrics, payment
        information, tax details, and cash management data.

        The transformation maintains the hierarchical structure of the report while
        converting internal data types to those suitable for API communication.

        Args:
            report_doc: The sales report document to transform

        Returns:
            BaseSalesReportResponse: Complete API response with all sales report data
        """
        # set SalesReportResponse fields from report_doc
        return BaseSalesReportResponse(
            tenant_id=report_doc.tenant_id,
            store_code=report_doc.store_code,
            terminal_no=report_doc.terminal_no,
            business_date=report_doc.business_date,
            open_counter=report_doc.open_counter,
            business_counter=report_doc.business_counter,
            # Transform gross sales metrics (total sales before returns/discounts)
            sales_gross=SalesReportTemplate(
                amount=report_doc.sales_gross.amount,
                quantity=report_doc.sales_gross.quantity,
                count=report_doc.sales_gross.count,
            ),
            # Transform net sales metrics (sales after returns/discounts)
            sales_net=SalesReportTemplate(
                amount=report_doc.sales_net.amount,
                quantity=report_doc.sales_net.quantity,
                count=report_doc.sales_net.count,
            ),
            # Transform line item discount metrics
            discount_for_lineitems=SalesReportTemplate(
                amount=report_doc.discount_for_lineitems.amount,
                quantity=report_doc.discount_for_lineitems.quantity,
                count=report_doc.discount_for_lineitems.count,
            ),
            # Transform subtotal discount metrics
            discount_for_subtotal=SalesReportTemplate(
                amount=report_doc.discount_for_subtotal.amount,
                quantity=report_doc.discount_for_subtotal.quantity,
                count=report_doc.discount_for_subtotal.count,
            ),
            # Transform returns metrics
            returns=SalesReportTemplate(
                amount=report_doc.returns.amount, quantity=report_doc.returns.quantity, count=report_doc.returns.count
            ),
            # Transform all tax information into a list of tax templates
            taxes=[
                TaxReportTemplate(
                    tax_name=tax.tax_name,
                    tax_amount=tax.tax_amount,
                    target_amount=tax.target_amount,
                    target_quantity=tax.target_quantity,
                )
                for tax in report_doc.taxes
            ],
            # Transform all payment information into a list of payment templates
            payments=[
                PaymentReportTemplate(payment_name=payment.payment_name, amount=payment.amount, count=payment.count)
                for payment in report_doc.payments
            ],
            # Transform cash balance information
            cash=CashBalanceReportTemplate(
                logical_amount=report_doc.cash.logical_amount,
                physical_amount=report_doc.cash.physical_amount,
                difference_amount=report_doc.cash.difference_amount,
                # Transform cash-in operations data
                cash_in=CashInOutReportTemplate(
                    amount=report_doc.cash.cash_in.amount, count=report_doc.cash.cash_in.count
                ),
                # Transform cash-out operations data
                cash_out=CashInOutReportTemplate(
                    amount=report_doc.cash.cash_out.amount, count=report_doc.cash.cash_out.count
                ),
            ),
            # Include formatted receipt and journal text for printing/display
            receipt_text=report_doc.receipt_text,
            journal_text=report_doc.journal_text,
        )
