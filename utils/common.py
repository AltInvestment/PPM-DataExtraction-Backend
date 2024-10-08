import os, re


def load_processed_file_ids(filename):
    processed_file_ids = set()
    if os.path.exists(filename):
        with open(filename, "r") as f:
            for line in f:
                processed_file_ids.add(line.strip())
    return processed_file_ids


def save_processed_file_ids(filename, processed_file_ids):
    with open(filename, "w") as f:
        for file_id in processed_file_ids:
            f.write(f"{file_id}\n")


def clean_extracted_data(data):
    """
    Cleans the extracted data from the LLM by removing code fences and extra text.
    """
    # Remove any leading/trailing whitespace
    data = data.strip()

    # If the data starts with ```json or ```python, remove the code fences
    if data.startswith("```"):
        data = data[data.find("\n") + 1 :]  # Remove the first line
        if data.endswith("```"):
            data = data[: data.rfind("```")]  # Remove the last ```
        data = data.strip()

    # Now extract the JSON object
    match = re.search(r"\{.*\}", data, re.DOTALL)
    if match:
        return match.group(0)
    else:
        # If no JSON object is found, return an empty JSON object
        return "{}"


sheet_headers = {
    "Leadership": [
        "Deal_ID",
        "Name",
        "Title",
        "Description",
        "Years_in_Industry",
        "Sponsor_Name_Rank",
    ],
    "Compensation": [
        "Deal_ID",
        "Type_of_Payment",
        "Determination_of_Amount",
        "Estimated_Amount",
        "Sponsor_Compensation_Rank",
    ],
    "Track Record": [
        "Program_Name",
        "PPM_Projected_Cash_on_Cash_Return_2023",
        "Avg_Cash_on_Cash_Return_from_Inception_through_12/31/2023",
        "Property_Type",
        "Deal_ID",
        "Sponsor_Record_Rank",
    ],
    "Use of Proceeds": [
        "Deal_ID",
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
        "Total",
        "LTV_%",
        "Syndication_Load_%",
    ],
    # We'll generate headers for "Projected Results" and "Final Data Table" dynamically
}

