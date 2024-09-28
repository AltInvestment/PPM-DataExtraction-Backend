from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()


# Process the PDF and create the vector store
def process_pdf_file(pdf_path):
    try:
        # Load the PDF document using PyPDFLoader
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        # Split the document into chunks for the vector store
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)

        # Create embeddings and vector store
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        vector_store = Chroma.from_documents(documents=splits, embedding=embeddings)

        return vector_store

    except Exception as e:
        logger.error(f"Failed to process PDF file {pdf_path}: {e}")
        return None


def extract_data_from_pdf(pdf_file_path, deal_id):
    vector_store = process_pdf_file(pdf_file_path)
    if vector_store:
        # Create the retriever from the vector store
        retriever = vector_store.as_retriever(k=10)

        loader = PyPDFLoader(pdf_file_path)
        documents = loader.load()
        first_10_pages = documents[:10]
        first_10_pages_text = "\n\n".join([doc.page_content for doc in first_10_pages])

        system_prompt = f"""
        # AI Assistant for Private Placement Memorandum (PPM) Information Extraction

        ## Task Overview:
        You are an AI assistant specialized in analyzing and extracting data from Private Placement Memorandum (PPM) documents, your task is to generate structured JSON output for six key sections: **Leadership**, **Compensation**, **Track Record**, **Projected Results**, **Use of Proceeds**, and the **Final Data Table**. The following principles and framework guide this process.

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
        {{context}}
        ---
        ### Important Notes:
        - Ensure all numeric **Deal_IDs** are enclosed in quotes (e.g., `"4444"`).  
        - Include percentage symbols (`%`) for all percentage values.  
        - If a value is not available or not applicable, use `"N/A"`.
        - You will be given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is.
        - Use the following as `Deal_ID`: {deal_id}
        """

        leadership_prompt = """ 
        # Leadership Section Prompt

        **Goal**: Extract leadership details from the PPM.

        **Instructions**:
        - Focus on identifying the individuals in leadership roles along with their titles, experience, and ranking within the sponsor organization.
        - The Description is created from the experiances of the person.
        - For years of experience, ensure it is explicitly mentioned; otherwise, mark it as `"N/A"`.
        - Follow the structure and format exactly as provided.

        **Structured Output**:
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
        If any information is missing or not explicitly provided, mark it as "N/A". 
        Ensure all values follow the format strictly (e.g., numeric years, proper strings for titles). 
        """

        compensation_prompt = """
        # Compensation Section Prompt

        **Goal**: Extract sponsor compensation details from the PPM.

        **Instructions**:
        - Extract only the compensation details related to the sponsor, including the type of payment, how it is determined, and the estimated amounts.
        - Use the exact format for all values, including strings and numeric amounts.

        **Context for Each Feild**:
        - Deal_ID: A unique identifier assigned to each investment deal.
        - Type_of_Payment: This describes the type or nature of the payment being made.
        - Determination_of_Amount: This field explains how the amount of the payment is determined.
        - Estimated_Amount: The estimated dollar amount of the payment or reimbursement. 
        - Sponsor_Compensation_Rank: This ranks the compensation relative to other types of payments the sponsor may receive. 

        **Structured Output**:
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
        If any information is not provided, use "N/A" in place of the missing value. 
        Do not infer missing values. 
        """

        track_record_prompt = """
        # Track Record Section Prompt

        **Goal**: Extract the sponsor's track record and return details from the PPM.

        **Instructions**:
        - Focus on extracting details like program name, projected and average returns, and property type.
        - Ensure that all return values follow the percentage format (e.g., `"5.00%"`).
        
        **Context for Each Feild**:
        - Deal_ID: A unique identifier assigned to each investment deal.
        - Program_Name: The name of the investment program
        - PPM_Projected_Cash_on_Cash_Return_2023: The projected cash-on-cash return for the year 2023, as stated in the Private Placement Memorandum (PPM). Cash-on-cash return measures the annual return on an investor's cash investment.
        - Avg_Cash_on_Cash_Return_from_Inception_through_12/31/2023: The average cash-on-cash return from the inception of the investment through the end of 2023. This metric provides a historical perspective on the investment's performance over time.
        - Property_Type: Describes the type of real estate property involved in the investment. 
        - Sponsor_Record_Rank: This indicates the sponsor's ranking or performance record for this deal, compared to others.

        **Structured Output**:
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
        If any data is not available, use "N/A" for missing values. 
        Ensure all numeric values follow the exact formatting with percentage symbols (%). 
        """

        projected_results_prompt = """
        # Projected Results Section Prompt

        **Goal**: Extract financial projections for the deal from the PPM.

        **Instructions**:
        - Focus on extracting yearly projected financial metrics from Year 1 to Year 11.
        - Ensure each field follows the exact format as shown, especially numeric fields and percentage values.
        
        **Context for Each Feild**:
        - Deal_ID: A unique identifier assigned to each investment deal.
        - Cash_on_Cash_Year_1 to Cash_on_Cash_Year_11: The cash-on-cash return for each year from Year 1 through Year 11. This measures the annual return the investor receives in relation to the amount of cash invested.
        - Ending_Balance_Year_1 to Ending_Balance_Year_11: The remaining balance or equity in the property at the end of each year.
        - Gross_Revenue_Year_1 to Gross_Revenue_Year_11: Total gross revenue generated by the property each year.
        - Total_Expenses_Year_1 to Total_Expenses_Year_11: The total expenses incurred each year.
        - NOI_Year_1 to NOI_Year_11: The net operating income for each year, calculated by subtracting operating expenses from gross revenue.
        
        **Structured Output**:
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
            },
            "Year_2": {
                "Cash_on_Cash": "5.50%",
                "Ending_Balance": "$376,000",
                "Gross_Revenue": "$9,000,000",
                "Total_Expenses": "$6,200,000",
                "NOI": "$2,800,000"
            }
            // Continue for all years up to Year_11
            }
        ]
        }
        If data for any year is not available, use "N/A" for missing values. 
        All numeric values should have dollar signs ($) or percentage symbols (%) where applicable. 
        """

        use_of_proceeds_prompt = """
        # Use of Proceeds Section Prompt

        **Goal**: Extract detailed use of proceeds from the PPM.

        **Instructions**:
        - Focus on extracting loan, equity, commissions, purchase price, reserves, and other fee information.
        - Ensure all values, including percentages and amounts, follow the exact format as shown.

        **Context for Each Feild**:
        - Deal_ID: A unique identifier assigned to each investment deal.
        - Sponsor: The entity or organization responsible for structuring and managing the investment deal.
        - Deal_Title: The name or title given to the investment opportunity or deal.
        - Disposition Fee: A fee charged by the sponsor at the time of selling the investment property.
        - Expected Hold (Years): The expected duration, in years, that the investment will be held before being sold or disposed of.
        - Zero Coupon: Indicates whether the investment includes a zero-coupon structure (Yes/No). A zero-coupon bond pays no periodic interest but is issued at a deep discount.
        - Lender_Type: The financial institution or lender providing financing for the deal.
        - Loan Term: The duration of the loan in years.
        - Gross Revenue: The total revenue generated by the property, measured in different years.
        - Total Expenses: The total operating expenses incurred by the property, also measured by year.
        - NOI (Net Operating Income): The income generated by the property after all operating expenses have been deducted. This is a key metric in real estate.
        - Cash on Cash Returns: The annual return on investment relative to the cash invested, reported for each year of the investment.
        - Loan Proceeds: The total loan amount received for financing the deal.
        - Loan Proceeds %: The percentage of the total deal value that is funded by the loan.
        - Equity Proceeds: The total equity raised from investors for the deal.
        - Equity Proceeds %: The percentage of the total deal value funded by investor equity.
        - Property Purchase Price: The price paid to acquire the investment property.
        - Property Purchase Price %: The property purchase price expressed as a percentage of the total project or deal cost.
        - Selling Commissions: Commissions paid to agents or brokers who facilitate the sale of the investment.
        - Selling Commissions %: The selling commissions expressed as a percentage of the total deal value.
        - Trust-Held Reserve: Funds held in reserve by the trust to cover potential future expenses.
        - Trust-Held Reserve %: The trust-held reserve expressed as a percentage of the total deal value.
        - Acquisition Fees: Fees paid to the sponsor for acquiring the property.
        - Acquisition Fees %: Acquisition fees expressed as a percentage of the total deal value.
        - Bridge Costs: Costs associated with bridge financing or interim loans used before the main financing is in place.
        - Bridge Costs %: Bridge costs expressed as a percentage of the total deal value.
        
        **Structured Output**:
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
            }
        ]
        }
        If any information is missing, mark it as "N/A". 
        Ensure percentages include the (%) symbol and amounts include the dollar sign ($). 
        """

        final_data_table_prompt = """
        # Final Data Table Section Prompt

        **Goal**: Extract the complete final data table, combining use of proceeds and financial projections.

        **Instructions**:
        - Extract all key financial metrics, lender information, and yearly projected data for the deal.
        - Ensure that all fields, especially numeric and percentage values, follow the exact format provided.
        - Make sure to fetch all the required data feilds.

        **Context for Each Feild**:
        - Deal_ID: A unique identifier assigned to each investment deal.
        - Sponsor: The entity or organization responsible for structuring and managing the investment deal.
        - Deal_Title: The name or title given to the investment opportunity or deal.
        - Disposition Fee: A fee charged by the sponsor at the time of selling the investment property.
        - Expected Hold (Years): The expected duration, in years, that the investment will be held before being sold or disposed of.
        - Zero Coupon: Indicates whether the investment includes a zero-coupon structure (Yes/No). A zero-coupon bond pays no periodic interest but is issued at a deep discount.
        - Lender_Type: The financial institution or lender providing financing for the deal.
        - Loan Term: The duration of the loan in years.
        - Gross Revenue: The total revenue generated by the property, measured in different years.
        - Total Expenses: The total operating expenses incurred by the property, also measured by year.
        - NOI (Net Operating Income): The income generated by the property after all operating expenses have been deducted. This is a key metric in real estate.
        - Cash on Cash Returns: The annual return on investment relative to the cash invested, reported for each year of the investment.
        - Loan Proceeds: The total loan amount received for financing the deal.
        - Loan Proceeds %: The percentage of the total deal value that is funded by the loan.
        - Equity Proceeds: The total equity raised from investors for the deal.
        - Equity Proceeds %: The percentage of the total deal value funded by investor equity.
        - Property Purchase Price: The price paid to acquire the investment property.
        - Property Purchase Price %: The property purchase price expressed as a percentage of the total project or deal cost.
        - Selling Commissions: Commissions paid to agents or brokers who facilitate the sale of the investment.
        - Selling Commissions %: The selling commissions expressed as a percentage of the total deal value.
        - Trust-Held Reserve: Funds held in reserve by the trust to cover potential future expenses.
        - Trust-Held Reserve %: The trust-held reserve expressed as a percentage of the total deal value.
        - Acquisition Fees: Fees paid to the sponsor for acquiring the property.
        - Acquisition Fees %: Acquisition fees expressed as a percentage of the total deal value.
        - Bridge Costs: Costs associated with bridge financing or interim loans used before the main financing is in place.
        - Bridge Costs %: Bridge costs expressed as a percentage of the total deal value.
        - Cash_on_Cash_Year_1 to Cash_on_Cash_Year_11: The cash-on-cash return for each year from Year 1 through Year 11. This measures the annual return the investor receives in relation to the amount of cash invested.
        - Ending_Balance_Year_1 to Ending_Balance_Year_11: The remaining balance or equity in the property at the end of each year.
        - Gross_Revenue_Year_1 to Gross_Revenue_Year_11: Total gross revenue generated by the property each year.
        - Total_Expenses_Year_1 to Total_Expenses_Year_11: The total expenses incurred each year.
        - NOI_Year_1 to NOI_Year_11: The net operating income for each year, calculated by subtracting operating expenses from gross revenue.
        
        **Structured Output**:
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
            "Year_1": {
                "Cash_on_Cash": "5.24%",
                "Ending_Balance": "$353,501",
                "Gross_Revenue": "$8,665,000",
                "Total_Expenses": "$5,999,750",
                "NOI": "$2,665,250"
            }
            // Continue for Year_2 to Year_11
            }
        ]
        }
        If any information is missing, use "N/A". 
        All numeric values should be formatted with dollar signs ($) or percentage symbols (%) as needed. 
        """

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt + "{context}"),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        # Initialize the LLM and memory
        llm = ChatOpenAI(model="gpt-4o-mini")

        contextualize_q_system_prompt = """
        Given the task of analyzing and extracting data from Private Placement Memorandum (PPM) documents, you will be provided with a chat history and the latest user question that may reference prior context. Your role is to reformulate the user's question into a standalone version that can be understood without relying on previous chat history or prior exchanges. Do NOT answer the question; only rephrase or return it as-is, ensuring it is clear and self-contained. Maintain the accuracy and integrity of the original query's intent.
        """

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        question_answer_chain = create_stuff_documents_chain(llm, prompt)

        rag_chain = create_retrieval_chain(
            history_aware_retriever, question_answer_chain
        )

        # Define your prompts for each section
        section_prompts = {
            "Leadership": leadership_prompt,
            "Compensation": compensation_prompt,
            "Track Record": track_record_prompt,
            "Projected Results": projected_results_prompt,
            "Use of Proceeds": use_of_proceeds_prompt,
            "Final Data Table": final_data_table_prompt,
        }

        # Extract data for each section in a conversational manner
        extracted_data = {}
        for section, prompt_text in section_prompts.items():
            # Here we pass input as a dict as expected by the RAG chain
            input_dict = {
                "input": prompt_text,
                "chat_history": [],
                "context": first_10_pages_text,  # Pass the first 10 pages as context
            }
            response = rag_chain.invoke(input_dict)
            # Extract only the answer part
            extracted_data[section] = response.get("answer", "No relevant data found.")

        # Save the extracted data to a .txt file
        with open(f"{pdf_file_path}_data.txt", "w") as f:
            for section, content in extracted_data.items():
                f.write(f"{content}\n\n")
        vector_store.delete_collection()
        logger.info("All sections have been successfully processed.")
        return extracted_data
    else:
        logger.error("Failed to create the vector store from the PDF.")
