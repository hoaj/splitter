from typing import Any
import anthropic


def situate_context(doc: str, chunk: str) -> tuple[str, Any]:
    DOCUMENT_CONTEXT_PROMPT = """
        <document>
        {doc_content}
        </document>
        """

    CHUNK_CONTEXT_PROMPT = """
        Here is the chunk we want to situate within the whole document
        <chunk>
        {chunk_content}
        </chunk>

        Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. The answer should be written in danish. Answer only with the succinct context written and nothing else.
        """

    client = anthropic.Anthropic()
    response = client.beta.prompt_caching.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=5000,
        temperature=0.0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": DOCUMENT_CONTEXT_PROMPT.format(doc_content=doc),
                        "cache_control": {
                            "type": "ephemeral"
                        },  # we will make use of prompt caching for the full documents
                    },
                    {
                        "type": "text",
                        "text": CHUNK_CONTEXT_PROMPT.format(chunk_content=chunk),
                    },
                ],
            },
        ],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )
    return response.content[0].text, response.usage
