from app.retsinformation.splitter import Split

splitter = Split(
    input_pdf="app/retsinformation/data/lejeloven.pdf",
    pdf_title="Lejeloven",
    markdown_output_file="app/retsinformation/data/lejeloven.md",
    json_output_file="app/retsinformation/data/lejeloven_chunks.json",
)
splitter.run()
