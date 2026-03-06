"""
Verification script for the fixed PDFService chunking logic.
Tests that tables are kept whole and text is properly split.
"""
import asyncio
from app.services.pdf_service import PDFService


def test_table_not_split():
    """Tables must never be cut in half by the text splitter."""
    print("=== Test: Tables are kept as whole parent chunks ===")
    service = PDFService(parent_chunk_size=100, parent_chunk_overlap=20)

    # Simulate a page with mixed text and a table
    pages = [{
        "page_number": 1,
        "elements": [
            (0, "text", "This is some introductory paragraph about quarterly results."),
            (100, "table", "| Quarter | Revenue | Profit |\n|---------|---------|--------|\n| Q1      | $100M   | $20M   |\n| Q2      | $120M   | $25M   |\n| Q3      | $110M   | $22M   |\n| Q4      | $130M   | $30M   |"),
            (300, "text", "The table above shows strong growth across all quarters with consistent margins."),
        ]
    }]

    chunks = service.chunk_hierarchical(pages)

    print(f"Total chunks: {len(chunks)}")
    table_chunks = [c for c in chunks if c["metadata"]["content_type"] == "table"]
    text_chunks = [c for c in chunks if c["metadata"]["content_type"] == "text"]

    print(f"Table chunks: {len(table_chunks)}")
    print(f"Text chunks: {len(text_chunks)}")

    # Table must be exactly 1 chunk (never split)
    assert len(table_chunks) == 1, f"Expected 1 table chunk, got {len(table_chunks)}"
    assert "| Quarter" in table_chunks[0]["content"], "Table content is missing"
    assert "| Q4" in table_chunks[0]["content"], "Table was truncated!"

    # Text should be split into children
    assert len(text_chunks) >= 1, "No text chunks created"

    print("PASSED: Table kept as single chunk\n")

    # Print all chunks for inspection
    for i, c in enumerate(chunks):
        ctype = c["metadata"]["content_type"]
        pid = c["metadata"]["parent_id"]
        print(f"  Chunk {i} [{ctype}] parent={pid}: {c['content'][:80]}...")
    print()


def test_text_hierarchy():
    """Text blocks must produce parent-child relationships."""
    print("=== Test: Text produces parent-child hierarchy ===")
    service = PDFService(parent_chunk_size=100, parent_chunk_overlap=20)

    pages = [{
        "page_number": 2,
        "elements": [
            (0, "text", "Artificial intelligence has transformed many industries. " * 5),
        ]
    }]

    chunks = service.chunk_hierarchical(pages)
    print(f"Total text chunks: {len(chunks)}")

    # All should have parent_content
    for c in chunks:
        assert c["metadata"]["parent_content"], "Missing parent_content!"
        assert c["metadata"]["is_child"] is True

    print("PASSED: All children have parent_content\n")


def test_no_duplication():
    """Elements should not be duplicated between table and text."""
    print("=== Test: No duplication between table and text ===")
    service = PDFService()

    pages = [{
        "page_number": 1,
        "elements": [
            (0, "text", "Hello world intro paragraph."),
            (50, "table", "| A | B |\n|---|---|\n| 1 | 2 |"),
            (100, "text", "Conclusion paragraph after table."),
        ]
    }]

    chunks = service.chunk_hierarchical(pages)

    # Count occurrences of table content across ALL chunks
    table_occurrences = sum(1 for c in chunks if "| A | B |" in c["content"])
    assert table_occurrences == 1, f"Table appears {table_occurrences} times (expected 1)"

    print("PASSED: No content duplication\n")


if __name__ == "__main__":
    test_table_not_split()
    test_text_hierarchy()
    test_no_duplication()
    print("All verification tests PASSED!")
