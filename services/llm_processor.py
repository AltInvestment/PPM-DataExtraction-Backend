from openai import OpenAI
import re
import logging
import colorlog
from utils.prompt import system_prompt


def setup_logger():
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )
    logger = colorlog.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger


logger = setup_logger()
logging.getLogger("pdfminer").setLevel(logging.WARNING)

from dotenv import load_dotenv
import json
from pdfminer.high_level import extract_text

load_dotenv()

client = OpenAI()


# Example function to interact with an LLM like GPT-4o-mini
def process_text_with_llm(extracted_text):
    try:
        # Define the prompt or query for the LLM
        system_prompt = """
You are tasked with extracting specific sections of information from a Private Placement Memorandum (PPM) document. The extracted data should be structured into JSON format according to the examples provided below. The data must be categorized into Leadership, Compensation, Track Record, Projected Results, Use of Proceeds, and Final Data Table sections.

Instructions:

1. Identify Key Sections:
   - Leadership
   - Compensation
   - Track Record
   - Projected Results
   - Use of Proceeds
   - Final Data Table

2. Data Extraction:
   For each identified section, extract the relevant data points according to the column descriptions provided. Ensure that all necessary fields are captured, and structure them within the corresponding JSON format.

3. Output Format:
   Each section should be outputted as a separate JSON object. The structure for each section is described below.

1. Leadership Section:
Extract details about the company's leadership team. Each leader's data should include:

- Deal_ID: Unique identifier for the deal, It will always be numeric.
- Name: The leader's full name.
- Title: Their position within the company.
- Description: A brief biography or description of their experience.
- Years_in_Industry: Number of years in the industry.
- Sponsor_Name_Rank: Ranking related to the sponsor.

Example JSON:
{
    "Leadership": [
        {
            "Deal_ID": "4444",
            "Name": "Edward E. Fernandez",
            "Title": "Chief Executive Officer",
            "Description": "Prior to founding 1031 Crowdfunding, Mr. Fernandez has 20 years of experience in real estate.",
            "Years_in_Industry": "20",
            "Sponsor_Name_Rank": "1"
        }
        // Additional leaders go here
    ]
}

2. Compensation Section:
Capture details about the compensation structures. Each compensation entry should include:

- Deal_ID: Unique identifier for the deal, It will always be numeric.
- Type_of_Payment: The type of payment or compensation.
- Determination_of_Amount: How the amount is determined.
- Estimated_Amount: The estimated amount.
- Sponsor_Compensation_Rank: Ranking related to compensation.

Example JSON:
{
    "Compensation": [
        {
            "Deal_ID": "4444",
            "Type_of_Payment": "Reimbursement of the Sponsor for Organization Expenses",
            "Determination_of_Amount": "The Sponsor is entitled to reimbursement for Organization Expenses...",
            "Estimated_Amount": "$275,000",
            "Sponsor_Compensation_Rank": "1"
        }
        // Additional compensation entries go here
    ]
}

3. Track Record Section:
Extract the company's past performance metrics. Each track record entry should include:

- Program_Name: The name of the investment program.
- PPM_Projected_Cash_on_Cash_Return_2023: Projected cash-on-cash return for 2023.
- Avg_Cash_on_Cash_Return_from_Inception_through_12/31/2023: Average cash-on-cash return from inception through the end of 2023.
- Property_Type: The type of property associated with the investment.
- Deal_ID: Unique identifier for the deal, It will always be numeric.
- Sponsor_Record_Rank: Ranking related to the sponsor's track record.

Example JSON:
{
    "Track Record": [
        {
            "Program_Name": "National Multifamily Portfolio I DST",
            "PPM_Projected_Cash_on_Cash_Return_2023": "5.00%",
            "Avg_Cash_on_Cash_Return_from_Inception_through_12/31/2023": "6.25%",
            "Property_Type": "Multifamily",
            "Deal_Id": "1010",
            "Sponsor_Record_Rank": "1"
        }
        // Additional track record entries go here
    ]
}

4. Projected Results Section:
Capture future financial projections. Each projected result entry should include year-by-year data:

- Deal_ID: Unique identifier for the deal, It will always be numeric.
- Year_X (e.g., Year_1, Year_2, etc.): The specific year of the projection.
  - Cash_on_Cash: Cash-on-cash return for the year.
  - Ending_Balance: Ending balance for the year.
  - Gross_Revenue: Gross revenue for the year.
  - Total_Expenses: Total expenses for the year.
  - NOI: Net Operating Income (NOI) for the year.

Example JSON:
{
    "Projected Results": [
        {
            "Deal_ID": "4444",
            "Year_1": {
                "Cash_on_Cash": "5.24%",
                "Ending_Balance": "$353,501",
                "Gross_Revenue": "$8,665,000",
                "Total_Expenses": "$5,999,750",
                "NOI": "$2,665,250"
            }
            // Additional years go here
        }
        // Additional projected results go here
    ]
}

5. Use of Proceeds Section:
Detail how the funds raised will be allocated. Each use of proceeds entry should include:

- Deal_ID: Unique identifier for the deal, It will always be numeric.
- Loan_Proceeds: The amount of loan proceeds.
- Loan_Proceeds_%: The percentage of loan proceeds relative to total proceeds.
- Equity_Proceeds: The amount of equity proceeds.
- Equity_Proceeds_%: The percentage of equity proceeds relative to total proceeds.
- Selling_Commissions: The amount allocated to selling commissions.
- Selling_Commissions_%: The percentage of selling commissions.
- Property_Purchase_Price: The total purchase price of the property.
- Property_Purchase_Price_%: The percentage of the purchase price relative to total proceeds.
- Trust_Held_Reserve: The amount reserved and held in trust.
- Trust_Held_Reserve_%: The percentage of the trust-held reserve.
- Acquisition_Fees: The fees associated with the acquisition.
- Acquisition_Fees_%: The percentage of acquisition fees.
- Bridge_Costs: The costs associated with bridge financing.
- Bridge_Costs_%: The percentage of bridge costs.
- Total: The total amount of proceeds.
- LTV_%: The loan-to-value ratio.
- Syndication_Load_%: The percentage of syndication load.

Example JSON:
{
    "Use of Proceeds": [
        {
            "Deal_ID": "4444",
            "Loan_Proceeds": "$14,960,000",
            "Loan_Proceeds_%": "32.91%",
            "Equity_Proceeds": "$30,500,000",
            "Equity_Proceeds_%": "67.09%",
            "Selling_Commissions": "$2,745,000",
            "Selling_Commissions_%": "6.04%",
            "Property_Purchase_Price": "$37,200,000",
            "Property_Purchase_Price_%": "81.83%",
            "Trust_Held_Reserve": "$600,000",
            "Trust_Held_Reserve_%": "1.32%",
            "Acquisition_Fees": "$423,000",
            "Acquisition_Fees_%": "1.50%",
            "Bridge_Costs": "$2,130,000",
            "Bridge_Costs_%": "4.64%",
            "Total": "$45,460,000",
            "LTV_%": "32.91%",
            "Syndication_Load_%": "18.17%"
        }
        // Additional use of proceeds entries go here
    ]
}

6. Final Data Table Section:
Extract comprehensive details for each deal. Each entry in the final data table should include:

- Deal_ID: Unique identifier for the deal, It will always be numeric.
- Sponsor: The sponsor's name.
- Deal_Title: Title of the deal.
- Disposition_Fee: Disposition fee as a percentage.
- Expected_Hold_Years: Expected hold period in years.
- Lender_Type: Type of lender (can be "N/A" if not applicable).
- Diversified: Indicates if the deal is diversified ("yes" or "no").
- 721_Upreit: Indicates if 721 Upreit is applicable ("yes", "no", or "optional").
- Distribution_Timing: Timing of distributions (e.g., "Monthly").
- Loan_Proceeds: The amount of loan proceeds.
- Loan_Proceeds_%: The percentage of loan proceeds relative to total proceeds.
- Equity_Proceeds: The amount of equity proceeds.
- Equity_Proceeds_%: The percentage of equity proceeds relative to total proceeds.
- Selling_Commissions: The amount allocated to selling commissions.
- Selling_Commissions_%: The percentage of selling commissions.
- Property_Purchase_Price: The total purchase price of the property.
- Property_Purchase_Price_%: The percentage of the purchase price relative to total proceeds.
- Trust_Held_Reserve: The amount reserved and held in trust.
- Trust_Held_Reserve_%: The percentage of the trust-held reserve.
- Acquisition_Fees: The fees associated with the acquisition.
- Acquisition_Fees_%: The percentage of acquisition fees.
- Bridge_Costs: The costs associated with bridge financing.
- Bridge_Costs_%: The percentage of bridge costs.
- Total: The total amount of proceeds.
- LTV_%: The loan-to-value ratio.
- Syndication_Load_%: The percentage of syndication load.
- Cash_on_Cash_Year_1: Cash-on-cash return for year 1.
- Ending_Balance_Year_1: Ending balance for year 1.
- Gross_Revenue_Year_1: Gross revenue for year 1.
- Total_Expenses_Year_1: Total expenses for year 1.
- NOI_Year_1: Net Operating Income for year 1.
- Cash_on_Cash_Year_11: Cash-on-cash return for year 11.
- Ending_Balance_Year_11: Ending balance for year 11.
- Gross_Revenue_Year_11: Gross revenue for year 11.
- Total_Expenses_Year_11: Total expenses for year 11.
- NOI_Year_11: Net Operating Income for year 11.
-- The year data column will be from year 1 to 11 
Example JSON:
{
    "Final Data Table": [
        {
            "Deal_ID": "4444",
            "Sponsor": "1031 CF",
            "Deal_Title": "1031CF Portfolio 4 DST",
            "Disposition_Fee": "4%",
            "Expected_Hold_Years": "7",
            "Lender_Type": "N/A",
            "Diversified": "no",
            "721_Upreit": "no",
            "Distribution_Timing": "Monthly",
            "Loan_Proceeds": "$14,960,000",
            "Loan_Proceeds_%": "32.91%",
            "Equity_Proceeds": "$30,500,000",
            "Equity_Proceeds_%": "67.09%",
            "Selling_Commissions": "$2,745,000",
            "Selling_Commissions_%": "6.04%",
            "Property_Purchase_Price": "$37,200,000",
            "Property_Purchase_Price_%": "81.83%",
            "Trust_Held_Reserve": "$600,000",
            "Trust_Held_Reserve_%": "1.32%",
            "Acquisition_Fees": "$423,000",
            "Acquisition_Fees_%": "1.50%",
            "Bridge_Costs": "$2,130,000",
            "Bridge_Costs_%": "4.64%",
            "Total": "$45,460,000",
            "LTV_%": "32.91%",
            "Syndication_Load_%": "18.17%"
            "Cash_on_Cash_Year_1": "5.24%",
            "Ending_Balance_Year_1": "$353,501",
            "Gross_Revenue_Year_1": "$8,665,000",
            "Total_Expenses_Year_1": "$5,999,750",
            "NOI_Year_1": "$2,665,250",
            "Cash_on_Cash_Year_2": "5.25%",
            "Ending_Balance_Year_2": "$329,935",
            "Gross_Revenue_Year_2": "$9,174,300",
            "Total_Expenses_Year_2": "$6,359,735",
            "NOI_Year_2": "$2,814,565",
            "Cash_on_Cash_Year_11": "N/A",
            "Ending_Balance_Year_11": "N/A",
            "Gross_Revenue_Year_11": "N/A",
            "Total_Expenses_Year_11": "N/A",
            "NOI_Year_11": "N/A"
        },
        // Additional final data table entries go here
    ]
}
"""

        # Call to the LLM API (example with OpenAI's GPT)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"{system_prompt}",
                },
                {
                    "role": "user",
                    "content": f"The following is the extracted text from the PPM Document:\n```{extracted_text_part1}```",
                },
            ],
        )

        # Process the response to extract relevant data
        processed_data = response.choices[0].message.content
        logger.info(processed_data)

        # Parse the processed data into the relevant sheets
        extracted_columns = parse_llm_response(processed_data)

        # Extract the last assistant message

        # Return the last assistant message
        return extracted_columns

    except Exception as e:
        logger.error(f"Failed to process text with LLM: {e}")
        return {}


def parse_llm_response(response_text):
    """
    Parse the response from LLM and map it to the respective sections as JSON objects.
    """
    try:
        # Attempt to parse the response text directly as JSON
        response_json = json.loads(response_text)

        # Assuming the LLM outputs the exact structure expected
        extracted_sections = {
            "Leadership": response_json.get("Leadership", []),
            "Compensation": response_json.get("Compensation", []),
            "Track Record": response_json.get("Track Record", []),
            "Projected Results": response_json.get("Projected Results", []),
            "Use of Proceeds": response_json.get("Use of Proceeds", []),
            "Final Data Table": response_json.get("Final Data Table", []),
        }

        return extracted_sections

    except json.JSONDecodeError:
        logger.error("Failed to parse LLM response as JSON.")
        return {}
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while parsing the LLM response: {e}"
        )
        return {}


# Function to clean the extracted text by removing extra spaces and newlines
def clean_extracted_text(text):
    # Remove leading and trailing whitespace
    cleaned_text = text.strip()
    # Replace multiple spaces with a single space
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)
    # Optionally, remove excessive newlines (e.g., replace multiple newlines with one)
    cleaned_text = re.sub(r"\n+", "\n", cleaned_text)
    return cleaned_text


# New function to process the PDF file
def process_pdf_file(pdf_path):
    try:
        # Extract text from the PDF
        extracted_text = extract_text(pdf_path)

        if extracted_text.strip():
            # Clean the extracted text
            cleaned_text = clean_extracted_text(extracted_text)

            # Process the cleaned text with the LLM
            extracted_columns = process_text_with_llm(cleaned_text)

            # Return or handle the extracted columns as needed
            return extracted_columns
        else:
            logger.error(f"No text extracted from PDF at {pdf_path}.")
            return {}

    except Exception as e:
        logger.error(f"Failed to process PDF file {pdf_path}: {e}")
        return {}


pdf_file_path = "tmp/PPM - Epoch Student Housing DST.pdf"
extracted_data = process_pdf_file(pdf_file_path)
logger.info(extracted_data)
