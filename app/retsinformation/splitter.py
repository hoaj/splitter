from app.util.helpers import Util
from app.retsinformation.helper import LocalUtil
import pathlib
import pdf4llm
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


class Split:
    def __init__(
        self, input_pdf: str, markdown_output_file: str, json_output_file: str
    ):
        self.input_pdf = input_pdf
        self.markdown_output_file = markdown_output_file
        self.json_output_file = json_output_file

    def convert_pdf_to_markdown(self) -> str:
        return pdf4llm.to_markdown(self.input_pdf)

    def save_markdown_to_file(self, markdown_document: str):
        pathlib.Path(self.markdown_output_file).write_bytes(markdown_document.encode())

    def split_markdown_document(self, markdown_document: str):
        headers_to_split_on = [
            ("#", "#"),
            ("##", "##"),
            ("###", "###"),
            # ("####", "####"),
            # ("#####", "#####"),
            # ("######", "######"),
        ]

        # MD splits
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on, strip_headers=True
        )
        splits = markdown_splitter.split_text(markdown_document)

        # Char-level splits
        chunk_size = 1500
        chunk_overlap = 100
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        splits = text_splitter.split_documents(splits)

        return splits

    def process_splits(self, splits):
        # Add page numbering to each doc
        splits = Util.append_headers_to_content(splits)
        splits = Util.add_missing_page_numbers(splits)
        splits = Util.remove_page_numbers_at_end(splits)
        splits = Util.remove_docs_without_alphabetic_content(splits)
        splits = Util.assign_unique_ids(splits)
        splits = Util.assign_souce_name(
            splits,
            "Lov om Ledningsejerregistret",
        )
        splits = Util.add_page_numbers_to_metadata(splits)
        return splits

    def run(self):
        # Convert PDF to markdown
        markdown_document = self.convert_pdf_to_markdown()
        markdown_document = Util.add_page_numbers(markdown_document)
        markdown_document = LocalUtil.format_header_retsinformation(markdown_document)
        self.save_markdown_to_file(markdown_document)

        # Split markdown document
        splits = self.split_markdown_document(markdown_document)

        # Process splits
        splits = self.process_splits(splits)

        # Situate context
        # splits = Util.append_situated_context(splits, markdown_document)

        # Save splits to JSON
        Util.save_data_to_json(splits, self.json_output_file)


if __name__ == "__main__":
    splitter = Split("data/lejeloven.pdf", "data/test.md", "data/test.json")
    splitter.run()
