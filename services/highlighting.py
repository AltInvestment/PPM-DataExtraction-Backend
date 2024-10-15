from utils.logger import logger
import pymupdf
import re
import json
from unidecode import unidecode


def highlight_text_in_pdf(pdf_path, extracted_data, output_pdf_path):

    def normalize_text(text):
        # Minimal normalization to match the PDF content
        text = unidecode(text)  # Convert accented characters to ASCII
        text = text.strip()
        return text

    def clean_json_content(content):
        # Remove code fences and any extra text
        content = content.strip()
        # Remove code fences if present
        content = re.sub(r"^```json\s*", "", content)
        content = re.sub(r"^```", "", content)
        content = re.sub(r"```$", "", content)
        return content

    # Define words to exclude from highlighting
    exclude_words = {"no", "yes", "n/a", "0"}

    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        logger.error(f"Failed to open PDF file {pdf_path}: {e}")
        return

    try:
        for section, content in extracted_data.items():
            if content == "No relevant data found.":
                continue

            # Clean the content to remove code fences and extra text
            content = clean_json_content(content)

            # Parse the JSON string into a Python object
            try:
                content = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON content for section {section}: {e}")
                continue

            if section == "Leadership":
                entries = content.get("Leadership", [])
                for entry in entries:
                    if isinstance(entry, dict):
                        name = normalize_text(entry.get("Name", ""))
                        if not name or name.lower() in exclude_words:
                            continue

                        for page_number in range(len(doc)):
                            try:
                                page = doc[page_number]
                                # Use case-insensitive search
                                text_instances = page.search_for(name)
                                if text_instances:
                                    for inst in text_instances:
                                        highlight = page.add_highlight_annot(inst)
                                        highlight.update()
                            except Exception as e:
                                logger.error(
                                    f"Failed to highlight '{name}' on page {page_number + 1}: {e}"
                                )

            elif section == "Compensation":
                entries = content.get("Compensation", [])
                for entry in entries:
                    if isinstance(entry, dict):
                        type_of_payment = normalize_text(
                            entry.get("Type_of_Payment", "")
                        )
                        estimated_amount = normalize_text(
                            entry.get("Estimated_Amount", "")
                        )
                        if (
                            not type_of_payment
                            or type_of_payment.lower() in exclude_words
                        ) and (
                            not estimated_amount
                            or estimated_amount.lower() in exclude_words
                        ):
                            continue

                        for page_number in range(len(doc)):
                            try:
                                page = doc[page_number]

                                if (
                                    type_of_payment
                                    and type_of_payment.lower() not in exclude_words
                                ):
                                    text_instances = page.search_for(type_of_payment)
                                    if text_instances:
                                        for inst in text_instances:
                                            highlight = page.add_highlight_annot(inst)
                                            highlight.update()
                                if (
                                    estimated_amount
                                    and estimated_amount.lower() not in exclude_words
                                ):
                                    text_instances = page.search_for(estimated_amount)
                                    if text_instances:
                                        for inst in text_instances:
                                            highlight = page.add_highlight_annot(inst)
                                            highlight.update()
                            except Exception as e:
                                logger.error(
                                    f"Failed to highlight Compensation on page {page_number + 1}: {e}"
                                )

            elif section == "Track Record":
                entries = content.get("Track Record", [])
                for entry in entries:
                    if isinstance(entry, dict):
                        program_name = normalize_text(entry.get("Program_Name", ""))
                        projected_return = normalize_text(
                            entry.get("PPM_Projected_Cash_on_Cash_Return_2023", "")
                        )
                        avg_return = normalize_text(
                            entry.get(
                                "Avg_Cash_on_Cash_Return_from_Inception_through_12/31/2023",
                                "",
                            )
                        )
                        for page_number in range(len(doc)):
                            try:
                                page = doc[page_number]

                                if (
                                    program_name
                                    and program_name.lower() not in exclude_words
                                ):
                                    text_instances = page.search_for(program_name)
                                    if text_instances:
                                        for inst in text_instances:
                                            highlight = page.add_highlight_annot(inst)
                                            highlight.update()
                                if (
                                    projected_return
                                    and projected_return.lower() not in exclude_words
                                ):
                                    text_instances = page.search_for(projected_return)
                                    if text_instances:
                                        for inst in text_instances:
                                            highlight = page.add_highlight_annot(inst)
                                            highlight.update()
                                if (
                                    avg_return
                                    and avg_return.lower() not in exclude_words
                                ):
                                    text_instances = page.search_for(avg_return)
                                    if text_instances:
                                        for inst in text_instances:
                                            highlight = page.add_highlight_annot(inst)
                                            highlight.update()
                            except Exception as e:
                                logger.error(
                                    f"Failed to highlight Track Record on page {page_number + 1}: {e}"
                                )

            elif section in ["Projected Results", "Use of Proceeds"]:
                entries = content.get(section, [])
                for entry in entries:
                    if isinstance(entry, dict):
                        for key, value in entry.items():
                            if isinstance(value, dict):
                                # For nested dictionaries like Yearly data
                                for sub_key, sub_value in value.items():
                                    value_normalized = normalize_text(sub_value)
                                    if (
                                        not value_normalized
                                        or value_normalized.lower() in exclude_words
                                    ):
                                        continue
                                    for page_number in range(len(doc)):
                                        try:
                                            page = doc[page_number]
                                            text_instances = page.search_for(
                                                value_normalized,
                                            )
                                            if text_instances:
                                                for inst in text_instances:
                                                    highlight = (
                                                        page.add_highlight_annot(inst)
                                                    )
                                                    highlight.update()
                                        except Exception as e:
                                            logger.error(
                                                f"Failed to highlight '{sub_value}' in {section} on page {page_number + 1}: {e}"
                                            )
                            elif isinstance(value, str) and any(
                                char.isdigit() for char in value
                            ):
                                value_normalized = normalize_text(value)
                                if (
                                    not value_normalized
                                    or value_normalized.lower() in exclude_words
                                ):
                                    continue
                                for page_number in range(len(doc)):
                                    try:
                                        page = doc[page_number]
                                        text_instances = page.search_for(
                                            value_normalized
                                        )
                                        if text_instances:
                                            for inst in text_instances:
                                                highlight = page.add_highlight_annot(
                                                    inst
                                                )
                                                highlight.update()

                                    except Exception as e:
                                        logger.error(
                                            f"Failed to highlight '{value}' in {section} on page {page_number + 1}: {e}"
                                        )

            elif section == "Final Data Table":
                entries = content.get("Final Data Table", [])
                for entry in entries:
                    if isinstance(entry, dict):
                        # Only highlight Disposition_Fee
                        disposition_fee = entry.get("Disposition_Fee", "")
                        if not disposition_fee:
                            continue
                        value_normalized = normalize_text(disposition_fee)
                        if (
                            not value_normalized
                            or value_normalized.lower() in exclude_words
                        ):
                            continue
                        for page_number in range(len(doc)):
                            try:
                                page = doc[page_number]
                                text_instances = page.search_for(value_normalized)
                                if text_instances:
                                    for inst in text_instances:
                                        highlight = page.add_highlight_annot(inst)
                                        highlight.update()
                            except Exception as e:
                                logger.error(
                                    f"Failed to highlight '{disposition_fee}' on page {page_number + 1}: {e}"
                                )

    except Exception as e:
        logger.error(f"Failed during the highlighting process: {e}")
    finally:
        try:
            doc.save(output_pdf_path, garbage=4, deflate=True)
            doc.close()
        except Exception as e:
            logger.error(f"Failed to save or close the PDF document: {e}")
