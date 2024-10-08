import os, json, ntpath

from services.google_services import append_to_google_sheets, delete_last_row
from services.llm_processor import extract_data_from_pdf
from utils.logger import logger
from utils.common import clean_extracted_data


def process_file(file_name, file_path, sheets_service, SPREADSHEET_ID, sheet_headers):
    # Assign a unique Deal_ID per document using the file name (without extension)
    deal_id = ntpath.basename(file_name)
    deal_id = os.path.splitext(deal_id)[0]  # Remove extension

    # Append 'Processing started' to 'Final Data Table' sheet
    sheet_name = "Final Data Table"
    headers = sheet_headers.get(sheet_name, [])
    num_columns = len(headers)
    if num_columns == 0:
        num_columns = 10  # default value
    processing_started_row = [deal_id, "Processing started"] + [""] * (num_columns - 2)
    append_to_google_sheets(
        sheets_service,
        SPREADSHEET_ID,
        sheet_name,
        [processing_started_row],
    )

    try:
        # Extract data from PDF, passing the Deal_ID
        extracted_columns = extract_data_from_pdf(file_path, deal_id)

        if extracted_columns:
            # -------------------------------
            # Merge Use of Proceeds into Final Data Table
            # -------------------------------
            if (
                "Final Data Table" in extracted_columns
                and "Use of Proceeds" in extracted_columns
            ):
                # Clean and parse the data
                final_data_table_data = clean_extracted_data(
                    extracted_columns["Final Data Table"]
                )
                use_of_proceeds_data = clean_extracted_data(
                    extracted_columns["Use of Proceeds"]
                )

                try:
                    final_data_table_json = json.loads(final_data_table_data)
                    use_of_proceeds_json = json.loads(use_of_proceeds_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON data: {e}")
                    # Proceed without merging
                else:
                    # Assuming there is only one item per Deal_ID
                    final_data_items = final_data_table_json.get("Final Data Table", [])
                    use_of_proceeds_items = use_of_proceeds_json.get(
                        "Use of Proceeds", []
                    )

                    # Build a mapping from Deal_ID to Use of Proceeds data
                    use_of_proceeds_mapping = {
                        item.get("Deal_ID", "N/A"): item
                        for item in use_of_proceeds_items
                    }

                    # Update Final Data Table items with data from Use of Proceeds
                    for final_item in final_data_items:
                        final_deal_id = final_item.get("Deal_ID", "N/A")
                        use_item = use_of_proceeds_mapping.get(final_deal_id)
                        if use_item:
                            # Update fields from Use of Proceeds
                            for key, value in use_item.items():
                                if key != "Deal_ID":
                                    if value and value != "N/A":
                                        final_item[key] = value
                                    else:
                                        final_item[key] = "N/A"
                                        pass
                        else:
                            # No matching Deal_ID in Use of Proceeds
                            pass

                    # Update the Final Data Table data
                    final_data_table_json["Final Data Table"] = final_data_items
                    # Update extracted_columns with the updated Final Data Table
                    extracted_columns["Final Data Table"] = json.dumps(
                        final_data_table_json
                    )
            # -------------------------------
            # End of merging
            # -------------------------------
            # -------------------------------
            # Merge Projected Results into Final Data Table
            # -------------------------------
            if (
                "Final Data Table" in extracted_columns
                and "Projected Results" in extracted_columns
            ):
                # Clean and parse the data
                final_data_table_data = clean_extracted_data(
                    extracted_columns["Final Data Table"]
                )
                projected_results_data = clean_extracted_data(
                    extracted_columns["Projected Results"]
                )

                try:
                    final_data_table_json = json.loads(final_data_table_data)
                    projected_results_json = json.loads(projected_results_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON data: {e}")
                    # Proceed without merging
                else:
                    # Assuming there is only one item per Deal_ID
                    final_data_items = final_data_table_json.get("Final Data Table", [])
                    projected_results_items = projected_results_json.get(
                        "Projected Results", []
                    )

                    # Build a mapping from Deal_ID to Projected Results data
                    projected_results_mapping = {
                        item.get("Deal_ID", "N/A"): item
                        for item in projected_results_items
                    }

                    # Update Final Data Table items with data from Projected Results
                    for final_item in final_data_items:
                        final_deal_id = final_item.get("Deal_ID", "N/A")
                        projected_item = projected_results_mapping.get(final_deal_id)
                        if projected_item:
                            # Update 'Year_N' data from Projected Results
                            for key, value in projected_item.items():
                                if key.startswith("Year_"):
                                    # Merge Year_N data
                                    if key in final_item:
                                        # If Year_N already exists in final_item, update its fields
                                        final_year_data = final_item[key]
                                        projected_year_data = value
                                        if isinstance(
                                            final_year_data, dict
                                        ) and isinstance(projected_year_data, dict):
                                            final_year_data.update(projected_year_data)
                                        else:
                                            final_item[key] = projected_year_data
                                    else:
                                        # Add the Year_N data
                                        final_item[key] = value
                                elif key != "Deal_ID":
                                    # Other keys, merge as needed
                                    if value and value != "N/A":
                                        final_item[key] = value
                                    else:
                                        final_item[key] = "N/A"
                                        pass
                        else:
                            # No matching Deal_ID in Projected Results
                            pass

                    # Update the Final Data Table data
                    final_data_table_json["Final Data Table"] = final_data_items
                    # Update extracted_columns with the updated Final Data Table
                    extracted_columns["Final Data Table"] = json.dumps(
                        final_data_table_json
                    )
            # -------------------------------
            # End of merging
            # -------------------------------
            # Append the processed data to the respective Google Sheets
            for sheet_name, data in extracted_columns.items():
                logger.info(f"Processing section: {sheet_name}")
                RANGE_NAME = (
                    f"{sheet_name}"  # We use the sheet name without cell reference
                )

                try:
                    # Clean the data to remove code fences and extra text
                    data = clean_extracted_data(data)

                    json_data = json.loads(data)
                    values = []

                    if sheet_name in json_data:
                        data_items = json_data[sheet_name]

                        # Ensure that Deal_ID is set for each item
                        for item in data_items:
                            item["Deal_ID"] = deal_id

                        if sheet_name == "Projected Results":
                            # Processing Projected Results
                            # Generate headers dynamically
                            base_headers = ["Deal_ID"]
                            years = []
                            for item in data_items:
                                years.extend(
                                    [
                                        key
                                        for key in item.keys()
                                        if key.startswith("Year_")
                                    ]
                                )
                            years = sorted(
                                set(years),
                                key=lambda x: int(x.replace("Year_", "")),
                            )

                            # Create headers
                            headers = base_headers
                            for year in years:
                                headers.extend(
                                    [
                                        f"{year}_Cash_on_Cash",
                                        f"{year}_Ending_Balance",
                                        f"{year}_Gross_Revenue",
                                        f"{year}_Total_Expenses",
                                        f"{year}_NOI",
                                    ]
                                )

                            # Prepare values
                            for item in data_items:
                                row = [item.get("Deal_ID", "N/A")]
                                for year in years:
                                    year_data = item.get(year, {})
                                    row.extend(
                                        [
                                            year_data.get("Cash_on_Cash", "N/A"),
                                            year_data.get("Ending_Balance", "N/A"),
                                            year_data.get("Gross_Revenue", "N/A"),
                                            year_data.get("Total_Expenses", "N/A"),
                                            year_data.get("NOI", "N/A"),
                                        ]
                                    )
                                values.append(row)
                            # Append data to Google Sheets
                            append_to_google_sheets(
                                sheets_service,
                                SPREADSHEET_ID,
                                RANGE_NAME,
                                values,
                            )

                        elif sheet_name == "Final Data Table":
                            # Processing Final Data Table
                            values = []
                            base_headers = [
                                "Deal_ID",
                                "Sponsor",
                                "Deal_Title",
                                "Disposition_Fee",
                                "Expected_Hold_Years",
                                "Lender_Type",
                                "Diversified",
                                "721_Upreit",
                                "Distribution_Timing",
                                "Gross_Proceeds",
                                "Gross_Proceeds_%",
                                "Loan_Proceeds",
                                "Loan_Proceeds_%",
                                "Equity_Proceeds",
                                "Equity_Proceeds_%",
                                "Selling_Commissions",
                                "Selling_Commissions_%",
                                "Property_Purchase_Price",
                                "Property_Purchase_Price_%",
                                "Trust_Held_Reserve",
                                "Trust_Held_Reserve_%",
                                "Acquisition_Fees",
                                "Acquisition_Fees_%",
                                "Bridge_Costs",
                                "Bridge_Costs_%",
                            ]
                            years = []
                            for item in data_items:
                                years.extend(
                                    [
                                        key
                                        for key in item.keys()
                                        if key.startswith("Year_")
                                    ]
                                )
                            years = sorted(
                                set(years),
                                key=lambda x: int(x.replace("Year_", "")),
                            )

                            # Create headers
                            headers = base_headers
                            for year in years:
                                headers.extend(
                                    [
                                        f"{year}_Cash_on_Cash",
                                        f"{year}_Ending_Balance",
                                        f"{year}_Gross_Revenue",
                                        f"{year}_Total_Expenses",
                                        f"{year}_NOI",
                                    ]
                                )

                            # Prepare values
                            for item in data_items:
                                row = [
                                    item.get("Deal_ID", "N/A"),
                                    item.get("Sponsor", "N/A"),
                                    item.get("Deal_Title", "N/A"),
                                    item.get("Website_Link", "N/A"),
                                    item.get("Date_Founded", "N/A"),
                                    item.get("Disposition_Fee", "N/A"),
                                    item.get("Expected_Hold_Years", "N/A"),
                                    item.get("Zero_Coupon", "N/A"),
                                    item.get("Lender_Type", "N/A"),
                                    item.get("Diversified", "N/A"),
                                    item.get("721_Upreit", "N/A"),
                                    item.get("Distribution_Timing", "N/A"),
                                    item.get("Gross_Proceeds", "N/A"),
                                    item.get("Gross_Proceeds_%", "N/A"),
                                    item.get("Loan_Proceeds", "N/A"),
                                    item.get("Loan_Proceeds_%", "N/A"),
                                    item.get("Equity_Proceeds", "N/A"),
                                    item.get("Equity_Proceeds_%", "N/A"),
                                    item.get("Property_Purchase_Price", "N/A"),
                                    item.get("Property_Purchase_Price_%", "N/A"),
                                    item.get("Total_Syndication_Load", "N/A"),
                                    item.get("Total_Syndication_Load_%", "N/A"),
                                    item.get("Selling_Commissions", "N/A"),
                                    item.get("Selling_Commissions_%", "N/A"),
                                    item.get("Trust_Held_Reserve", "N/A"),
                                    item.get("Trust_Held_Reserve_%", "N/A"),
                                    item.get("Acquisition_Fees", "N/A"),
                                    item.get("Acquisition_Fees_%", "N/A"),
                                    item.get("Bridge_Costs", "N/A"),
                                    item.get("Bridge_Costs_%", "N/A"),
                                    item.get("Other_Fees", "N/A"),
                                    item.get("Other_Fees_%", "N/A"),
                                    item.get("GS_Property_Number", "N/A"),
                                    item.get("GS_Location", "N/A"),
                                    item.get("GS_Zip_Code_Grade", "N/A"),
                                    item.get("GS_Supply_Barriers", "N/A"),
                                    item.get("GS_Business_Friendliness", "N/A"),
                                    item.get("Market_Description", "N/A"),
                                ]
                                for year in years:
                                    year_data = item.get(year, {})
                                    row.extend(
                                        [
                                            year_data.get("Cash_on_Cash", "N/A"),
                                            year_data.get("Ending_Balance", "N/A"),
                                            year_data.get("Gross_Revenue", "N/A"),
                                            year_data.get("Total_Expenses", "N/A"),
                                            year_data.get("NOI", "N/A"),
                                        ]
                                    )
                                values.append(row)
                                delete_last_row(
                                    sheets_service, SPREADSHEET_ID, sheet_name
                                )
                                # Instead of appending, update the row where Deal_ID matches
                                append_to_google_sheets(
                                    sheets_service,
                                    SPREADSHEET_ID,
                                    sheet_name,
                                    values,
                                )

                        elif sheet_name == "Use of Proceeds":
                            # For Use of Proceeds section
                            headers = sheet_headers.get(sheet_name, [])
                            for item in data_items:
                                row = [item.get(header, "N/A") for header in headers]
                                values.append(row)
                            # Append data to Google Sheets
                            append_to_google_sheets(
                                sheets_service,
                                SPREADSHEET_ID,
                                RANGE_NAME,
                                values,
                            )

                        elif sheet_name == "Leadership":
                            # Processing Leadership section
                            headers = sheet_headers.get(sheet_name, [])
                            values = []

                            # Check if data_items are present
                            if not data_items:
                                logger.warning(
                                    f"No data found for Leadership section in {file_name}"
                                )
                                continue

                            logger.info(f"Leadership Data: {data_items}")

                            for item in data_items:
                                row = [item.get(header, "N/A") for header in headers]
                                values.append(row)

                            try:
                                # Append data to Google Sheets
                                append_to_google_sheets(
                                    sheets_service,
                                    SPREADSHEET_ID,
                                    RANGE_NAME,
                                    values,
                                )
                                logger.info(f"Appended Leadership data for {file_name}")
                            except Exception as e:
                                logger.error(f"Error appending Leadership data: {e}")

                        elif sheet_name == "Compensation":
                            # Processing Compensation section
                            headers = sheet_headers.get(sheet_name, [])
                            for item in data_items:
                                row = [item.get(header, "N/A") for header in headers]
                                values.append(row)
                            # Append data to Google Sheets
                            append_to_google_sheets(
                                sheets_service,
                                SPREADSHEET_ID,
                                RANGE_NAME,
                                values,
                            )

                        elif sheet_name == "Track Record":
                            # Processing Track Record section
                            headers = sheet_headers.get(sheet_name, [])
                            for item in data_items:
                                row = [item.get(header, "N/A") for header in headers]
                                values.append(row)
                            # Append data to Google Sheets
                            append_to_google_sheets(
                                sheets_service,
                                SPREADSHEET_ID,
                                RANGE_NAME,
                                values,
                            )

                        else:
                            # For any other sections not explicitly handled
                            logger.warning(
                                f"Unrecognized section: {sheet_name}. Skipping."
                            )

                    else:
                        logger.error(
                            f"Section {sheet_name} not found in the extracted data."
                        )
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON data for {sheet_name}: {e}")
                except Exception as e:
                    logger.error(
                        f"An error occurred while processing {sheet_name}: {e}"
                    )
            logger.info(f"Successfully processed file: {file_name}")
        else:
            # Extraction failed; update the row with an error message
            delete_last_row(sheets_service, SPREADSHEET_ID, "Final Data Table")
            error_row = [deal_id, "Extraction failed"] + [""] * (num_columns - 2)
            append_to_google_sheets(
                sheets_service,
                SPREADSHEET_ID,
                sheet_name,
                [error_row],
            )
            logger.error("Failed to extract data from %s.", file_name)
    except Exception as e:
        # An exception occurred; remove the last row and append error message
        delete_last_row(sheets_service, SPREADSHEET_ID, "Final Data Table")
        error_row = [deal_id, f"Processing error: {str(e)}"] + [""] * (num_columns - 2)
        append_to_google_sheets(
            sheets_service,
            SPREADSHEET_ID,
            sheet_name,
            [error_row],
        )
        logger.error("An error occurred while processing %s: %s", file_name, e)
