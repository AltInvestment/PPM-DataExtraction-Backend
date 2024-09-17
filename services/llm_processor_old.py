from openai import OpenAI
import re
import logging
import colorlog
import pathlib


# from utils.prompt import system_prompt


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

from dotenv import load_dotenv
import json
import pymupdf4llm

load_dotenv()

client = OpenAI()


# Example function to interact with an LLM like GPT-4o-mini
def process_text_with_llm(extracted_text):
    try:
        # Define the prompt or query for the LLM
        system_prompt = """
# AI Assistant for Private Placement Memorandum (PPM) Information Extraction

#### Task Overview:
As an AI assistant specialized in analyzing and extracting data from Private Placement Memorandum (PPM) documents, your task is to generate structured JSON output for six key sections: **Leadership**, **Compensation**, **Track Record**, **Projected Results**, **Use of Proceeds**, and the **Final Data Table**. The following principles and framework guide this process.

---

### Core Principles:
1. **Accuracy**: Extract data precisely as it appears in the source document.
2. **Completeness**: Ensure all required fields are populated for each section.
3. **Consistency**: Maintain uniform formatting and structure across all entries.
4. **Adaptability**: Handle variations in data presentation while preserving the core information.

---

### Operational Framework:

#### 1. **Information Extraction Process**:
a) Carefully read and analyze the entire PPM document.  
b) Identify the six key sections: **Leadership**, **Compensation**, **Track Record**, **Projected Results**, **Use of Proceeds**, and **Final Data Table**.  
c) Locate and extract all relevant data points for each section based on the field descriptions.  
d) If a required field is not explicitly stated, use contextual information to infer the value or mark it as `"N/A"` if it cannot be determined.

#### 2. **Data Structuring**:
a) Organize the extracted data into **JSON format** for each section.  
b) Ensure all required fields are included, even if the value is `"N/A"` or empty.  
c) Maintain consistent data types (e.g., numeric values for years, percentages as strings with the `%` symbol).

#### 3. **Output Generation**:
a) Present each section as a **separate JSON object**.  
b) Use the exact field names and structure as provided in the examples below.  
c) Include all extracted entries for each section.

---

### Section Specifications:

#### 1. **Leadership Section**:
- **Fields**: Deal_ID, Name, Title, Description, Years_in_Industry, Sponsor_Name_Rank
- **Example**:
  ```json
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
    ]
  }
  ```

#### 2. **Compensation Section**:
- **Fields**: Deal_ID, Type_of_Payment, Determination_of_Amount, Estimated_Amount, Sponsor_Compensation_Rank
- **Example**:
  ```json
  {
    "Compensation": [
      {
        "Deal_ID": "4444",
        "Type_of_Payment": "Reimbursement of the Sponsor for Organization Expenses",
        "Determination_of_Amount": "The Sponsor is entitled to reimbursement for Organization Expenses...",
        "Estimated_Amount": "$275,000",
        "Sponsor_Compensation_Rank": "1"
      }
    ]
  }
  ```

#### 3. **Track Record Section**:
- **Fields**: Program_Name, PPM_Projected_Cash_on_Cash_Return_2023, Avg_Cash_on_Cash_Return_from_Inception_through_12/31/2023, Property_Type, Deal_ID, Sponsor_Record_Rank
- **Example**:
  ```json
  {
    "Track Record": [
      {
        "Program_Name": "National Multifamily Portfolio I DST",
        "PPM_Projected_Cash_on_Cash_Return_2023": "5.00%",
        "Avg_Cash_on_Cash_Return_from_Inception_through_12/31/2023": "6.25%",
        "Property_Type": "Multifamily",
        "Deal_ID": "1010",
        "Sponsor_Record_Rank": "1"
      }
    ]
  }
  ```

#### 4. **Projected Results Section**:
- **Fields**: Deal_ID, Year_X (X from 1 to 11, each containing Cash_on_Cash, Ending_Balance, Gross_Revenue, Total_Expenses, NOI(Net Operating Income))
- **Example**:
  ```json
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
      }
    ]
  }
  ```

#### 5. **Use of Proceeds Section**:
- **Fields**: Deal_ID, Loan_Proceeds, Loan_Proceeds_%, Equity_Proceeds, Equity_Proceeds_%, Selling_Commissions, Selling_Commissions_%, Property_Purchase_Price, Property_Purchase_Price_%, Trust_Held_Reserve, Trust_Held_Reserve_%, Acquisition_Fees, Acquisition_Fees_%, Bridge_Costs, Bridge_Costs_%, Total, LTV_%, Syndication_Load_%
- **Example**:
  ```json
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
    ]
  }
  ```

#### 6. **Final Data Table Section**:
- **Fields**: All fields from Use of Proceeds section, plus Deal_ID, Sponsor, Deal_Title, Disposition_Fee, Expected_Hold_Years, Lender_Type, Diversified, 721_Upreit, Distribution_Timing, and all fields from Projected Results for Year_1 to Year_11.
- **Example**:
  ```json
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
        "Syndication_Load_%": "18.17%",
        "Year_1": {
          "Cash_on_Cash": "5.24%",
          "Ending_Balance": "$353,501",
          "Gross_Revenue": "$8,665,000",
          "Total_Expenses": "$5,999,750",
          "NOI": "$2,665,250"
        }
        // Additional years go here (Year_2 to Year_11)
      }
    ]
  }
  ```

---

### Important Notes:
- Ensure all numeric **Deal_IDs** are enclosed in quotes (e.g., `"4444"`).  
- Include percentage symbols (`%`) for all percentage values.  
- If a value is not available or not applicable, use `"N/A"`.  
- For the **Final Data Table**, include data for all years from **Year_1 to Year_11**, even if some years are `"N/A"`.
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
                    "content": f"The following is the extracted text from the PPM Document:\n```\n{extracted_text}\n```\n--Make sure to extract all the information",
                },
            ],
            max_tokens=16384,
        )

        # Process the response to extract relevant data
        processed_data = response.choices[0].message.content

        with open("processed_data.txt", "w") as file:
            file.write(processed_data)

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


def clean_extracted_text(text):
    # List of section titles to remove (as keywords)
    unwanted_sections = [
        "Risk Factors",
        "Legal Disclaimers",
        "Who May Invest",
        "How to Subscribe",
        "Plan of Distribution",
        "CONFLICTS OF INTEREST",
        "Conflicts of Interest",
        "Litigation",
        "Litigation and Legal Proceedings",
        "Excess Business Losses May Not Be Currently Deductible",
        "Limit on Business Interest Deductions",
        "FEDERAL INCOME TAX CONSEQUENCES",
        "Classification for Purposes of Section 1031",
        "Property Identification for Section 1031 Exchanges",
        "Receipt of Boot",
        "Forward–Looking Statements",
        "Deduction for Qualified Business Income",
        "Subordination",
        "Covenants, Representations and Warranties",
        "Tax Deficiency, Penalties and Interest",
        "Taxable Income",
        "Net Income and Loss of Each Investor",
        "Tax Impact of Sale of the Property",
        "State and Local Laws",
        "THE OFFERING",
        "Investor Suitability Requirements",
        "Fee Waivers, Special Sales",
        "REPORTS AND ADDITIONAL INFORMATION",
        "Books and Records",
        "Tax Information",
        "Additional Information",
        "Instructions to Investor Questionnaire & Purchase Agreement",
        "INSTRUCTIONS TO INVESTORS FOR PURCHASING INTERESTS:",
        "Corporation, 2901 Butterfield Road, Oak Brook, Illinois 60523, Attention: Investments, or via e-mail to",
        "investments@inlandprivatecapital.com.",
        "A.",
        "IF THE INVESTOR IS AN INDIVIDUAL, PLEASE COMPLETE THE FOLLOWING:",
        "Each investor must initial the statement or statements below that truthfully describe him or her:",
        "After completing this page, you may proceed to page 8.",
        "B.",
        "IF THE INVESTOR IS A TRUST, PLEASE COMPLETE THE FOLLOWING:",
        "Please select the appropriate type of trust below and initial accordingly.",
        "Revocable Trusts: Please initial the statement or statements below that truthfully describe the purchaser:",
        "Irrevocable Trusts: Please initial the statement below that truthfully describes the purchaser:",
        "C.",
        "IF THE INVESTOR IS AN ENTITY (CORPORATION, PARTNERSHIP, LLC, ETC.), PLEASE",
        "COMPLETE THE FOLLOWING:",
        "partnership, the investor must submit the following: (1) a copy of the Partnership",
        "Please initial the statement or statements below that truthfully describe the purchaser:",
        "Please provide additional pages as necessary to complete this Section II for all equity owners.",
        "Please direct distributions: (Select one.)",
        "________________________________________________________________________________",
        "SECTION I – OWNERSHIP AND INVESTMENT INFORMATION",
        "COMPLETE THE FOLLOWING:",
        "INVESTOR #1 (SPOUSE #1, TRUSTEE #1, EQUITY OWNER #1, ETC.)",
        "INVESTOR #2 (SPOUSE #2, TRUSTEE #2, EQUITY OWNER #2, ETC.)",
        "SECTION III – INVESTOR DISTRIBUTION OPTIONS",
        "  Checking    Savings",
        "Electronic Deposit (ACH) Authorization – I (we) authorize the Seller’s manager and signatory trustee (the “Manager”), to deposit",
        "The signature(s) of all investors of record are required.",
        "Executed this ____ day of ___________________, 20____",
        "SIGNATURE PAGE TO INVESTOR QUESTIONNAIRE –",
        "ALL AUTHORIZED PERSONS MUST SIGN.",
        "I (we) acknowledge and agree to all of the representations and warranties contained in this Investor Questionnaire.",
        "If a natural person:",
        "If not a natural person:",
        "ALL AUTHORIZED PERSONS MUST SIGN THIS PAGE.",
        "SIGNATURE PAGE TO THE TRUST AGREEMENT OF EPOCH STUDENT HOUSING",
        "EPOCH",
        "STUDENT HOUSING DST, dated December 1, 2023, as may be further amended or supplemented from time",
        "SECTION IV – SUBSTITUTE W–9",
        "TO BE COMPLETED BY INDIVIDUAL/ENTITY FOR WHICH INFORMATION WILL BE",
        "REPORTED TO THE IRS.",
        "DST",
        "ON BEHALF OF OR BY INDIVIDUAL INVESTOR(S):",
        "ON BEHALF OF OR BY OTHER ENTITY (trust, corporation, partnership, limited liability company):",
        "APPENDIX A – TRUST CERTIFICATE",
        "Note: To be completed only by those investors investing through a trust.",
        "Please select one of the following three options:",
        "EPOCH STUDENT HOUSING DST is authorized by the terms of the Trust",
        "All trustees must sign and date below.",
        "Note: To be completed only by those investors investing through a corporation.",
        "Additional Note: Appendix D may be provided as an alternative to this Appendix C.",
        "WHEREAS, the Corporation is authorized to execute and deliver all documents relating to the Investment;",
        "WHEREAS, the Board of Directors believes it to be in the best interest of the Corporation to make the",
        "NOW THEREFORE, BE IT RESOLVED,",
        "FURTHER RESOLVED,",
        "FURTHER RESOLVED, that the Officer is hereby authorized and directed to execute, deliver and",
        "FURTHER RESOLVED, that any action heretofore taken and all documentation heretofore delivered by",
        "Additional Note: Appendix C may be provided as an alternative to this Appendix D.",
        "Note: To be completed only by those investors investing through a partnership.",
        "Note: To be completed only by those investors investing through a limited liability company.",
        "APPENDIX B – INCUMBENCY CERTIFICATE",
        "APPENDIX C – CORPORATE RESOLUTION",
        "APPENDIX D – OFFICER'S CERTIFICATE",
        "APPENDIX E – PARTNERSHIP RESOLUTION",
        "APPENDIX F – LIMITED LIABILITY COMPANY RESOLUTION",
        "CONFIDENTIAL",
        "IMPORTANT NOTES",
        "The Trust Agreement",
        "Agreement”). Epoch Student Housing Exchange, L.L.C., a Delaware limited liability company and an affiliate of",
        "The Offering",
        "IMPORTANT NOTE TO PROSPECTIVE INVESTORS: No prospective Investor will be able to",
        "acquire an Interest in the Trust until the following events have occurred: (1) the Trust has obtained the Loan;",
        "(2) the Master Lease has been amended and restated to incorporate the terms of the Loan; (3) the Trust",
        "Agreement has been amended and restated to incorporate the terms of the Loan; and (4) the Trust has entered",
        "into the Asset Management Agreement (collectively, the “Closing Events”). This Memorandum will be",
        "supplemented (such supplement, the “Closing Supplement”) to disclose the occurrence of the Closing Events",
        "as soon as practicable following the date on which such events have occurred (the “Closing Date”).",
        "POTENTIAL INVESTORS SHOULD CAREFULLY CONSIDER THE FOLLOWING",
        "Each prospective Investor should consult with his, her or its own tax advisor regarding an investment",
        "in the Interests and the qualification of his, her or its transaction under Section 1031 for his, her or its specific",
        "circumstances. Each prospective Investor’s specific circumstances may differ and, as a result, no assurances",
        "can be given and no legal opinion will be provided that the purchase of the Interests by any prospective Investor",
        "will qualify as a Section 1031 Exchange.",
        "An investment in Interests involves significant risk and is suitable only for Investors who have",
        "adequate financial means, desire a relatively long-term investment and who will not need immediate liquidity",
        "from their investment and can afford to lose their entire investment. The risks involved with an investment in",
        "The Interests have not been approved or disapproved by the SEC or the securities regulatory authority",
        "of any state, nor has the SEC or any securities regulatory authority of any state passed upon the accuracy or",
        "adequacy of this Memorandum. Any representation to the contrary is a criminal offense.",
        "The Interests are being offered only to persons who are “accredited investors,” as defined in Rule",
        "501(a) of Regulation D under the Securities Act of 1933, as amended (the “Securities Act”) and any",
        "corresponding provisions of state securities laws.",
        "The Interests have not been, and will not be, registered under the Securities Act or any state securities",
        "laws. The Interests will be offered and sold pursuant to an exemption from the registration requirements of the",
        "Securities Act, in accordance with Rule 506(b) of Regulation D, and in compliance with any applicable state",
        "securities laws. The Interests will not be offered or sold in any state in which such offers or sales are not qualified",
        "or otherwise exempt from registration. The Trust reserves the right to reject any offer to purchase the Interests.",
        "In addition, the Trust reserves the right to cancel any sale at any time prior to the receipt of funds for purchase,",
        "if that sale, in the opinion of the Trust and its counsel, may violate any federal or state securities law or",
        "regulation or is otherwise objectionable for whatever reason. The Interests are subject to restrictions on",
        "transferability and resale and you will not be able to transfer or resell Interests or any beneficial interest therein",
        "unless the Interests are registered pursuant to or exempted from such registration requirements. Investors",
        "must be prepared to bear the economic risk of an investment in the Interests for an indefinite period of time",
        "and be able to withstand a total loss of their investment.",
        "Neither the Trust, the Sponsor, nor any of their respective affiliates has authorized any person to make",
        "any representations or furnish any information with respect to the Interests or the Property, other than as set",
        "forth in this Memorandum or other documents or information the Trust or the Sponsor may furnish to",
        "Investors. Investors are encouraged to ask the Trust or the Sponsor questions concerning the terms and",
        "conditions of this Offering and the Property.",
        "The Sponsor has prepared this Memorandum solely for the benefit of persons interested in acquiring",
        "Interests. The recipient of this Memorandum agrees to keep the contents of this Memorandum confidential and",
        "not to duplicate or furnish copies of this Memorandum to any person other than such recipient’s advisors, and",
        "further agrees promptly to return this Memorandum to the Trust at the address below if: (1) the recipient",
        "decides not to purchase the Interests; (2) the recipient’s purchase offer is rejected; or (3) the Offering is",
        "A WARNING ABOUT FORWARD–LOOKING STATEMENTS",
        "MARKET DATA",
        "Terms",
        "Master Lease",
        "Disposition Services Agreement",
        "Right of First Opportunity Agreement",
        "Risks Related to the Delaware Statutory Trust Structure",
        "Risks Related to the Property",
        "Risks Related to the Anticipated Financing",
        "Risks Related to the Master Lease and the Management of the Property",
        "Risks Related to the Offering",
        "Tax Risks",
        "COMPENSATION TO IPC, ITS AFFILIATED PARTIES AND THE PROPERTY MANAGER",
        "Location and General Description of the Property",
        "Detailed Description of the Buildings",
        "Physical Condition of the Property",
        "Immediate Repairs – Immediate repairs are those repairs that are beyond the scope of regular maintenance",
        "Flood Zone",
        "Seismic Zone",
        "Wind Zone",
        "Environmental",
        "Agreements Affecting the Property",
        "General",
        "SUMMARY OF THE TRUST AGREEMENT",
        "Purposes and Term of the Trust",
        "Authority and Duties of the Trustees",
        "Compensation to the Trustees",
        "Limitation on Authority of the Trustees",
        "Authority of Investors",
        "Distributions",
        "Restrictions on Transfer of Interests",
        "Property Rights",
        "Sale or Exchange of the Property",
        "Transfer Distribution and Springing LLC",
        "Investor Liability and Bankruptcy",
        "Tax Status of the Trust",
        "Non–Disclosure of Information",
        "MARKET ANALYSIS AND OVERVIEW",
        "Regional Analysis",
        "Neighborhood Analysis",
        "Market Analysis",
        "ACQUISITION OF THE PROPERTY",
        "ANTICIPATED FINANCING TERMS",
        "Basic Terms",
        "Terms of the Earn–Out Advance",
        "Prepayment",
        "Insurance, Casualty and Condemnation",
        "Lender Reserve Account",
        "Events of Default",
        "Nonrecourse Loan",
        "Environmental Indemnity",
        "Guaranty Agreement",
        "PROPERTY MANAGEMENT",
        "The Property Management Agreement and Other Arrangements",
        "Resolution of Conflicts of Interest",
        "The Placement Agent",
        "Introduction",
        "The Investor understands that the tax consequences of an investment in the Interests, especially the",
        "qualification of the transaction under Section 1031 and the related rules, are complex and vary with the facts",
        "and circumstances particular to the Investor. Therefore, the Investor represents and warrants that he, she or",
        "it: (1) has consulted with his, her or its own independent tax advisor regarding the investment in the Interests",
        "and the qualification of the transaction under Section 1031; (2) except to the extent of the Tax Opinion rendered",
        "by Special Tax Counsel, is not relying on the Trust, any of its affiliates or agents, including its counsel and",
        "accountants, for any tax advice regarding the qualification of the transaction under Section 1031 or any other",
        "matter; and (3) is not relying on any statements made in this Memorandum regarding the qualification of his,",
        "her or its purchase of the Interests under Section 1031.",
        "How to Purchase the Interests",
        "IMPORTANT NOTE TO PROSPECTIVE INVESTORS: No prospective Investor will be able to acquire an",
        "Interest in the Trust until the Closing Date, which is the date on which all of the following events have occurred:",
        "(1) the Trust has obtained the Loan; (2) the Master Lease has been amended and restated to incorporate the",
        "terms of the Loan; (3) the Trust Agreement has been amended and restated to incorporate the terms of the",
        "Loan; and (4) the Trust has entered into the Asset Management Agreement. If the Trust receives your Investor",
        "Questionnaire & Purchase Agreement prior to the Closing Date, it will hold your Investor Questionnaire &",
        "Purchase Agreement, but it will not accept any payment for the purchase of the Interests, until the Closing",
        "Date. The Trust will begin accepting payment of the purchase price for the Interests immediately following the",
        "issuance of the Closing Supplement.",
        "Closing",
        "Submission of Offer to Purchase",
        "No Tax Advice",
        "Termination of the Investor Questionnaire & Purchase Agreement",
        "Indemnity",
        "Fees",
        "Broker/Dealer Disqualifying Events",
        "EPOCH STUDENT HOUSING DST",
        "EXHIBIT A",
        "Name of Investor: _________________________________________________________________",
        "Type of Investment:",
        "Amount of Equity Investment: $_______________________________",
        "Funds to Close: Please indicate how you will be purchasing your interest.",
        "accepted.",
        "Investor Questionnaire (attached): please complete, sign and date.",
        "Purchase Agreement (attached): please complete, sign and date.",
        "Entity Documentation (i.e., trust certificate and trust agreement, as amended; corporate",
        "For questions or assistance, please contact (888) 671-1031 or investments@inlandprivatecapital.com.",
        "INVESTMENT APPROVAL – EPOCH STUDENT HOUSING DST",
        "Name of Investor(s):",
        "Investment Amount:",
        "Name of Advisor or",
        "Representative:",
        "Name of Broker Dealer",
        "or Firm:",
        "Advisor/Rep. Address:",
        "City, State, Zip:",
        "Phone:",
        "Advisor/Rep Email:",
        "Firm Principal Email:",
        "IMPORTANT DISCLOSURE – PLEASE READ AND ACKNOWLEDGE BY SIGNING BELOW",
        "The investment provided for herein is approved pursuant to the terms and conditions of the executed Soliciting Dealer",
        "Agreement or Registered Investment Advisor Agreement for the Offering. Each of the undersigned parties hereby",
        "represents and warrants that he or she will comply with the applicable requirements of the Securities Act of 1933, as",
        "amended, and the published rules and regulations of the Securities and Exchange Commission thereunder, and applicable",
        "blue sky or other state securities laws, as well as the rules and regulations of FINRA or any other applicable regulatory",
        "authority. Each of the undersigned parties further represents and warrants that he or she is not subject to any of the “Bad",
        "Actor” disqualifications described in Rule 506(d) under the Securities Act of 1933, as amended, except for such event: (1)",
        "contemplated by Rule 506(d)(2) of the Securities Act of 1933, as amended, and (2) a reasonably detailed written description",
        "of which has been furnished to the placement agent of the offering",
        "Firm Principal:",
        "Advisor/Representative:",
        "PURCHASE AGREEMENT",
        "PURCHASE AGREEMENT OF EPOCH STUDENT HOUSING DST",
        "Up to $77,167,152 of Interests",
        "HOUSING DST, a Delaware statutory trust (the “Seller”) and the undersigned, with reference to the facts set forth below.",
        "RECITALS",
        "Placement Memorandum”), beneficial ownership interests in the Seller (the “Interests”).",
        "made payable to “EPOCH STUDENT HOUSING DST” for the aggregate purchase price of the Interests. The minimum",
        "The Seller shall not accept any payment of the purchase price for the Interests and shall not close on",
        "the purchase of any Interests until the following events have occurred: (1) the Trust has obtained the",
        "Loan; (2) the Master Lease has been amended and restated to incorporate the terms of the Loan; (3)",
        "the Trust Agreement has been amended and restated to incorporate the terms of the Loan; and (4)",
        "the Trust has entered into the Asset Management Agreement (collectively, the “Closing Events”).",
        "This Memorandum will be supplemented (such supplement, the “Closing Supplement”) to disclose",
        "the occurrence of the Closing Events as soon as practicable following the date on which such events",
        "have occurred (the “Closing Date”). The Seller agrees to hold this Purchase Agreement on behalf of",
        "the undersigned, and will not accept or otherwise receive any payment of the purchase price for the",
        "Interests from the undersigned in connection therewith, until the Closing Date.",
        "Once the Closing Events have occurred, the Seller will take the following steps:",
        "(i)",
        "If the investment is part of a Section 1031 tax-deferred exchange, the Seller will advise the",
        "undersigned’s qualified intermediary that the Closing Events have occurred, and the",
        "Seller and the qualified intermediary will coordinate the payment for the purchase of the",
        "Interests in accordance with Section 2 of this Purchase Agreement.",
        "(ii)",
        "If the investment is not part of a Section 1031 tax-deferred exchange, the Seller will advise",
        "the undersigned’s financial professional that the Closing Events have occurred, and the",
        "financial professional will coordinate with the undersigned the payment for the purchase",
        "of the Interests in accordance with Section 2 of this Purchase Agreement.",
        "The Seller will not accept or otherwise receive any payment of the purchase price for the Interests from the",
        "undersigned prior to the Closing Date.",
        "Notwithstanding anything to the contrary herein, the undersigned reserves the right to withdraw any Investor",
        "Questionnaire & Purchase Agreement submitted prior to the Closing Date, on the terms described herein. Specifically,",
        "the undersigned may revoke his, her or its Investor Questionnaire & Purchase Agreement prior to the close of the",
        "fifth business day after the Seller issues a Supplement to the Private Placement Memorandum, confirming that the",
        "Closing Events have occurred (such date referred to herein as the “Revocation Deadline”), by providing written notice",
        "of revocation to the Seller prior to the Revocation Deadline. If the undersigned notifies the Seller of his or her desire",
        "to revoke the Investor Questionnaire & Purchase Agreement in a timely manner, the Seller will promptly return the",
        "Investor Questionnaire & Purchase Agreement to the undersigned. The undersigned’s right to withdraw the Investor",
        "Questionnaire & Purchase Agreement terminates as of the Revocation Deadline.",
        "The undersigned understands that the Seller has not obtained a specific Private Letter ruling from",
        "the Internal Revenue Service (“IRS”) addressing the treatment of the Interests in this Offering for income tax",
        "purposes, including but not limited to whether an Interest is “of like kind” to real estate for purposes of Section 1031",
        "or is “similar or related in service or use” to involuntarily converted property of the undersigned for purposes of",
        "Internal Revenue Code section 1033 (“Section 1033”). In addition,",
        "the undersigned understands that the tax",
        "consequences of an investment in the Interests, especially the qualification of the transaction under Section 1031 or",
        "Section 1033 of the Code and the related rules, are complex and vary with the facts and circumstances of each",
        "individual. Therefore, the undersigned represents and warrants that he or she: (1) has independently obtained advice",
        "from legal counsel and/or accountants about a tax-deferred exchange under Section 1031 or a conversion under",
        "Section 1033 and applicable state laws, including, without limitation, whether the acquisition of an Interest may",
        "qualify as part of a tax-deferred exchange or involuntary conversion, and he or she relying on such advice; (2)",
        "understands that the Seller has not obtained a ruling from the IRS addressing the treatment of the Interests in this",
        "Offering for income tax purposes, including but not limited to whether an Interest is “of like kind” to real estate for",
        "purposes of Section 1031 or is “similar or related in service or use” to involuntarily converted property of the",
        "undersigned for purposes of Section 1033; (3) understands that the tax consequences of an investment in an Interest,",
        "especially the treatment of the transaction under Section 1031 and the related Section 1031 exchange rules, or under",
        "Section 1033 and its underlying rules, are complex and vary with the facts and circumstances of each individual",
        "purchaser; and (4) understands that the opinion of Seyfarth Shaw, LLP, as special tax counsel to the Seller, is only",
        "Seyfarth Shaw, LLP’s view of the anticipated tax treatment, and there is no guarantee that the IRS will agree with",
        "such opinion.",
        "and warranties apply only to those investors purchasing Interests as part of a Section 1031 tax-deferred exchange.",
        "The Interests have not been approved or disapproved by the Securities and Exchange Commission, or any",
        "state securities commission or other regulatory authority, nor have any of the foregoing authorities passed",
        "upon or endorsed the merits of this Offering or the accuracy or adequacy of the Private Placement",
        "Memorandum. Any representation to the contrary is unlawful. The Interests offered hereby are subject to",
        "investment risk, including the possible loss of principal.",
        "I (we) acknowledge and agree to all of the representations and warranties contained in this Purchase",
        "Agreement.",
        "SELLER",
        "Executed this ____ day of _____________________,",
        "20___",
        "EPOCH STUDENT HOUSING DST, a Delaware",
        "Statutory Trust",
        "BUYER",
        "The Trust and the Property",
        "decision.",
        "Management Agreement”) with Epoch Student Housing Exchange, L.L.C., a Delaware limited liability company",
        "Acquisition and Anticipated Financing of the Property",
        "Out Advance”), which funds will be retained in the Trust Reserve Account and used for repairs and replacements to",
        "Price Ratio associated with this Offering are based on the Initial Advance ($56,400,000), which represents the",
        "portion of the Loan that will be funded as of the date of the closing of the Loan (the “Loan Closing Date”) and",
        "(b) the financial forecast set forth in Exhibit D, the Forecasted Statement of Cash Flows, takes into account",
        "both the amount of the Initial Advance ($56,400,000) and the maximum Earn-Out Advance ($5,100,000, which",
        "is expected to be funded no later than the Final Commitment Expiration Date). If the maximum Earn-Out",
        "Advance is not funded in accordance with the Loan Documents, the cash-on-cash returns to Investors beginning",
        "in the year of such funding and thereafter may differ from the forecast for such period set forth in Exhibit D.",
        "terminated prior to a purchase by the recipient.",
        "This Memorandum contains summaries of certain agreements and other documents. Although the",
        "Sponsor believes these summaries are accurate, potential Investors should refer to the actual agreements and",
        "documents available in the Digital Investor Kit for more complete information about the rights, obligations and",
        "other matters in the agreements and documents. In addition, prospective Investors are strongly encouraged to",
        "have independent legal counsel closely review this Memorandum and all documents referenced herein and",
        "attached hereto, including, but not limited to, the Loan Documents.",
        "The mailing address of the Trust is Epoch Student Housing DST, c/o Investor Services, Inland Private",
        "Capital Corporation, 2901 Butterfield Road, Oak Brook, Illinois 60523, and the telephone number is (866) My-",
        "Inland ((866) 694-6526).",
        "A WARNING ABOUT FORWARD-LOOKING STATEMENTS",
        "MARKET DATA",
        "LEGENDS",
        "NOTICE TO INVESTORS IN ALL U.S. STATES",
        "IN MAKING AN INVESTMENT DECISION, INVESTORS MUST RELY ON THEIR OWN",
        "EXAMINATION OF THIS MEMORANDUM AND THE TERMS OF THE OFFERING, INCLUDING THE",
        "MERITS AND RISKS INVOLVED. THESE SECURITIES HAVE NOT BEEN RECOMMENDED BY ANY",
        "UNITED STATES FEDERAL OR STATE SECURITIES COMMISSION OR REGULATORY",
        "AUTHORITY. FURTHERMORE, THE FOREGOING AUTHORITIES HAVE NOT CONFIRMED THE",
        "ACCURACY OR DETERMINED THE ADEQUACY OF THIS DOCUMENT. ANY REPRESENTATION",
        "TO THE CONTRARY IS A CRIMINAL OFFENSE.",
        "THESE SECURITIES ARE SUBJECT TO RESTRICTIONS ON TRANSFERABILITY AND",
        "RESALE AND MAY NOT BE TRANSFERRED OR RESOLD EXCEPT AS PERMITTED UNDER THE",
        "UNITED STATES SECURITIES ACT OF 1933, AS AMENDED, AND THE APPLICABLE STATE",
        "SECURITIES LAWS, PURSUANT TO REGISTRATION OR EXEMPTION THEREFROM. INVESTORS",
        "SHOULD BE AWARE THAT THEY MAY BE REQUIRED TO BEAR THE FINANCIAL RISKS OF THE",
        "INVESTMENT FOR AN INDEFINITE PERIOD OF TIME.",
        "ADDITIONAL NOTICE TO FLORIDA INVESTORS",
        "IF SALES ARE MADE TO FIVE OR MORE PERSONS IN FLORIDA, AND YOU PURCHASE",
        "SECURITIES HEREUNDER, THEN YOU MAY VOID SUCH PURCHASE EITHER WITHIN THREE",
        "DAYS AFTER THE FIRST TENDER OF CONSIDERATION IS MADE BY YOU TO THE ISSUER, AN",
        "AGENT OF THE ISSUER, OR AN ESCROW AGENT OR WITHIN THREE DAYS AFTER THE",
        "AVAILABILITY OF THIS PRIVILEGE IS COMMUNICATED TO YOU, WHICHEVER OCCURS LATER.",
        "EXHIBITS",
        "THE DOCUMENTS THAT ARE AVAILABLE IN THE DIGITAL INVESTOR KIT ARE",
        "IMPORTANT TO THE INVESTORS’ REVIEW OF THE OFFERING. IF YOU ARE NOT",
        "ABLE TO ACCESS THE DIGITAL INVESTOR KIT, PLEASE CONTACT IPC",
        "IMMEDIATELY.",
    ]

    # Use regex to remove unwanted sections from the text
    for section in unwanted_sections:
        # Escape any special characters in the section titles
        escaped_section = re.escape(section)
        # Regex to match sections that start with **SectionName**, # SectionName, ## SectionName, ### SectionName, or #### SectionName
        text = re.sub(
            rf"(?m)(^(\*\*{escaped_section}\*\*|[#]+ {escaped_section})\s*\n).*?(?=^(\*\*|\#|\Z))",
            "",
            text,
            flags=re.DOTALL,
        )

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
        extracted_text = pymupdf4llm.to_markdown(pdf_path)

        pathlib.Path("output.md").write_bytes(extracted_text.encode())

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


pdf_file_path = "../tmp/PPM - Epoch Student Housing DST.pdf"
extracted_data = process_pdf_file(pdf_file_path)
logger.info(extracted_data)
