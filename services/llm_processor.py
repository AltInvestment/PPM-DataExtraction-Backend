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
from utils.prompts import (
    system_prompt,
    leadership_prompt,
    compensation_prompt,
    final_data_table_prompt,
    projected_results_prompt,
    track_record_prompt,
    use_of_proceeds_prompt,
)
from services.highlighting import highlight_text_in_pdf

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
    try:
        vector_store = process_pdf_file(pdf_file_path)
        if vector_store:
            # Create the retriever from the vector store
            retriever = vector_store.as_retriever(k=15)

            loader = PyPDFLoader(pdf_file_path)
            documents = loader.load()
            first_few_pages = documents[:20]
            first_few_pages_text = "\n\n".join(
                [
                    doc.page_content.replace("{", "{{").replace("}", "}}")
                    for doc in first_few_pages
                ]
            )
            last_10_pages = documents[-10:]
            last_10_pages_text = "\n\n".join(
                [
                    doc.page_content.replace("{", "{{").replace("}", "}}")
                    for doc in last_10_pages
                ]
            )

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        system_prompt(
                            deal_id=deal_id, first_few_pages_text=first_few_pages_text
                        ),
                    ),
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
                "Projected Results": projected_results_prompt(
                    last_10_pages_text=last_10_pages_text
                ),
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
                }
                response = rag_chain.invoke(input_dict)
                # Extract only the answer part
                extracted_data[section] = response.get(
                    "answer", "No relevant data found."
                )

            # Highlight text in the PDF according to extracted data
            output_pdf_path = f"{pdf_file_path}_highlighted.pdf"
            highlight_text_in_pdf(pdf_file_path, extracted_data, output_pdf_path)

            # Save the extracted data to a .txt file
            with open(f"{pdf_file_path}_data.txt", "w") as f:
                for section, content in extracted_data.items():
                    f.write(f"{section}:\n")
                    if isinstance(content, list):
                        for entry in content:
                            f.write(f"{entry}\n")
                    else:
                        f.write(f"{content}\n")
                    f.write("\n")

            vector_store.delete_collection()
            logger.info("All sections have been successfully processed.")
            return extracted_data
        else:
            logger.error("Failed to create the vector store from the PDF.")
    except Exception as e:
        logger.error(f"Failed to extract data from PDF {pdf_file_path}: {e}")
        return None
