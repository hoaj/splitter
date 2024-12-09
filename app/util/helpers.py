import json
import re
import uuid
from typing import Any, Dict, List
from langchain_core.documents import Document
from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter
from .contextual_chunks import situate_context
from tqdm import tqdm


class Util:
    # Define the format string for the page number text
    page_format = "\n_Page {} starts_\n"

    @staticmethod
    def add_page_numbers(text: str) -> str:
        # Add initial page number
        text = Util.page_format.format(1) + text

        # Define the regex pattern to find "-----" with line breaks before and after
        pattern = r"(?<=\n\n)-----(?=\n\n)"

        # Find all occurrences of the pattern
        matches = list(re.finditer(pattern, text))

        # Remove the last occurrence if it exists
        if matches:
            last_match = matches[-1]
            start, end = last_match.span()
            text = text[:start] + text[end:]

        # Initialize the page number
        page_number = 2

        # Function to replace each match with the corresponding page number
        def replacer(match):
            nonlocal page_number
            replacement = Util.page_format.format(page_number)
            page_number += 1
            return replacement

        # Use re.sub with the replacer function to replace each match
        result = re.sub(pattern, replacer, text)

        return result

    @staticmethod
    def add_missing_page_numbers(docs: List[Document]) -> List[Document]:
        page_pattern = r"_Page (\d+) starts_"
        last_known_page_number = 1

        for doc in docs:
            page_content = doc.page_content

            # Check if the page_content starts with a page number
            if not re.match(page_pattern, page_content.lstrip()):
                # If not, and if we have a last_known_page_number, prepend it
                if last_known_page_number is not None:
                    prepend_page_number = Util.page_format.format(
                        last_known_page_number
                    )
                    page_content = prepend_page_number + page_content.lstrip()

            # Find all occurrences of page numbers in the page_content
            page_numbers_in_content = re.findall(page_pattern, page_content)
            if page_numbers_in_content:
                # Update last_known_page_number for each found number
                for num in page_numbers_in_content:
                    last_known_page_number = num

            # Update the doc.page_content with the modified page_content
            doc.page_content = page_content

        return docs

    @staticmethod
    def remove_page_numbers_at_end(docs: List[Document]) -> List[Document]:
        # Define the regex pattern to find "Side xxxx starter:" at the end of the content
        page_pattern = r"_Page (\d+) starts_\s*$"

        # Iterate through the documents
        for doc in docs:
            page_content = doc.page_content.strip()

            # Check if the page_content ends with a page number
            if re.search(page_pattern, page_content):
                # Remove the page number at the end
                page_content = re.sub(page_pattern, "", page_content).strip()

            # Update the doc.page_content with the modified page_content
            doc.page_content = page_content

        return docs

    @staticmethod
    def append_headers_to_content(docs: List[Document]) -> List[Document]:
        for doc in docs:
            headers = [f"{key} {value}" for key, value in doc.metadata.items()]
            headers_text = "\n".join(headers)
            doc.page_content = headers_text + "\n" + doc.page_content
        return docs

    @staticmethod
    def remove_docs_without_alphabetic_content(docs: List[Document]) -> List[Document]:
        alphabetic_pattern = re.compile(r"[a-zA-Z]")
        return [doc for doc in docs if alphabetic_pattern.search(doc.page_content)]

    @staticmethod
    def save_data_to_json(data: Any, output_file: str):
        class CustomEncoder(json.JSONEncoder):
            def default(self, obj):
                if hasattr(obj, "__dict__"):
                    return obj.__dict__
                return super().default(obj)

        # Check if data is a string and convert it to a dictionary
        if isinstance(data, str):
            data = {"text": data}

        with open(output_file, "w") as file:
            json.dump(data, file, indent=2, ensure_ascii=False, cls=CustomEncoder)

    @staticmethod
    def metadata_func(json_obj: Dict, default_metadata: Dict) -> Dict:
        metadata = json_obj.get("metadata", {})
        # metadata = default_metadata.copy()
        # metadata.update(json_obj.get("metadata", {}))
        return metadata

    @staticmethod
    def load_docs(file_path: str) -> List[Document]:
        loader = JSONLoader(
            file_path=file_path,
            jq_schema=".[]",
            metadata_func=Util.metadata_func,
            content_key=".page_content",
            is_content_key_jq_parsable=True,
        )

        data = loader.load()
        return data

    @staticmethod
    def get_all_metadata_values_for_a_key(docs: List[Document], key: str) -> List[Any]:
        values = set()
        for doc in docs:
            if key in doc.metadata:
                values.add(doc.metadata[key])
        return list(values)

    @staticmethod
    def format_retrived_docs(docs: list[Document]) -> str:
        formatted_content = ""
        for doc in docs:
            formatted_content += doc.page_content + "\n\n"
        return formatted_content.strip()

    @staticmethod
    def assign_unique_ids(docs: List[Document]) -> List[Document]:
        for doc in docs:
            if "id" in doc.__dict__:
                del doc.__dict__["id"]
            if "type" in doc.__dict__:
                del doc.__dict__["type"]
            doc.metadata["id"] = str(uuid.uuid4())
        return docs

    @staticmethod
    def assign_souce_name(docs: List[Document], source_name: str) -> List[Document]:
        for doc in docs:
            doc.metadata["source_name"] = source_name
        return docs

    @staticmethod
    def add_page_numbers_to_metadata(docs: List[Document]) -> List[Document]:
        page_pattern = re.compile(r"_Page (\d+) starts_")

        for doc in docs:
            page_numbers = page_pattern.findall(doc.page_content)
            doc.metadata["page_numbers"] = [int(num) for num in page_numbers]

        return docs

    @staticmethod
    def append_situated_context(
        docs: List[Document], markdown_document: str
    ) -> List[Document]:
        total_input_tokens = 0
        total_output_tokens = 0
        total_cache_creation_input_tokens = 0
        total_cache_read_input_tokens = 0

        section_split = "###"
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[(section_split, section_split)],
            strip_headers=False,
        )
        chapter_splits = markdown_splitter.split_text(markdown_document)

        for doc in tqdm(docs, desc="Appending situated context"):

            section = Util.get_metadata_by_key(doc, section_split)
            if section is None:
                continue
            related_chapter = Util.get_page_content_by_metadata_pairs(
                chapter_splits, section_split, section
            )
            if related_chapter is None:
                continue

            context, usage = situate_context(related_chapter, doc.page_content)
            doc.page_content += f"\n\n{context}"
            doc.metadata["context"] = context

            # Accumulate cache performance metrics
            total_input_tokens += usage.input_tokens
            total_output_tokens += usage.output_tokens
            total_cache_creation_input_tokens += usage.cache_creation_input_tokens
            total_cache_read_input_tokens += usage.cache_read_input_tokens

        # Print summarized cache performance metrics
        print(f"Total input tokens: {total_input_tokens}")
        print(f"Total output tokens: {total_output_tokens}")
        print(f"Total cache creation input tokens: {total_cache_creation_input_tokens}")
        print(f"Total cache read input tokens: {total_cache_read_input_tokens}")

        return docs

    @staticmethod
    def get_metadata_by_key(doc: Document, key: str) -> str:
        return doc.metadata.get(key)

    @staticmethod
    def get_page_content_by_metadata_pairs(
        docs: List[Document], key: str, value: Any
    ) -> str:
        for doc in docs:
            if doc.metadata.get(key) == value:
                return doc.page_content
        return None
