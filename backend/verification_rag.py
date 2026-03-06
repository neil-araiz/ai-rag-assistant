"""
Final verification for the row-to-sentence table conversion logic.
Simulates the 3 table types from the user's screenshots.
"""
from app.services.pdf_service import PDFService
from unittest.mock import MagicMock


def test_sentence_conversion():
    """Test _table_to_sentences with simulated table data matching user's PDF."""
    service = PDFService()

    # --- Image 2: Short-value grid (Domain/Strands Per Quarter) ---
    print("=== Image 2 Type: Short-Value Grid ===")
    mock_table = MagicMock()
    mock_table.extract.return_value = [
        ["", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10"],
        ["1st Quarter", "Matter", "Matter", "Matter", "Matter", "Matter", "Force, Motion, & Energy", "Living Things and Their Environment", "Earth & Space"],
        ["2nd Quarter", "Living Things and Their Environment", "Living Things and Their Environment", "Living Things and Their Environment", "Living Things and Their Environment", "Living Things and Their Environment", "Earth & Space", "Matter", "Force, Motion, & Energy"],
    ]
    result = service._table_to_sentences(mock_table)
    print(result)
    assert "1st Quarter" in result
    assert "Matter" in result
    assert "G3" in result
    print("PASSED\n")

    # --- Image 3: Complex multi-column with nested content ---
    print("=== Image 3 Type: Complex Curriculum Table ===")
    mock_table2 = MagicMock()
    mock_table2.extract.return_value = [
        ["CONTENT", "CONTENT STANDARDS", "PERFORMANCE STANDARDS", "LEARNING COMPETENCY", "CODE", "LEARNING MATERIALS", "SCIENCE EQUIPMENT"],
        ["1. Properties\n1.1 Characteristics of solids, liquids, and gases", "The learners demonstrate understanding of...", "The learners should be able to...", "1. describe different objects based on their characteristics", "S3MT-Ia-b-1", "BEAM 5. Unit 4.\nLearning Guides. 3 Materials.", "1. 5-Newton Spring Balance\n2. Beral Pipette Dropper"],
    ]
    result2 = service._table_to_sentences(mock_table2)
    print(result2)
    assert "CONTENT" in result2
    assert "S3MT-Ia-b-1" in result2
    print("PASSED\n")

    # --- Image 1: Text-heavy table (Spiralling) ---
    print("=== Image 1 Type: Text-Heavy Table ===")
    mock_table3 = MagicMock()
    mock_table3.extract.return_value = [
        ["Grade 3", "Grade 4", "Grade 5", "Grade 6"],
        [
            "When learners observe different objects and materials, they become aware of their different characteristics such as shape, weight, definiteness of volume and ease of flow.",
            "Aside from being grouped into solids, liquids, or gases, materials may also be grouped according to their ability to absorb water.",
            "After learning how to read and interpret product labels, learners can critically decide whether these materials are harmful or not.",
            "In Grade 4, the learners have observed the changes when mixing a solid in a liquid or a liquid in another liquid."
        ],
    ]
    result3 = service._table_to_sentences(mock_table3)
    print(result3)
    assert "Grade 3" in result3
    assert "observe" in result3
    print("PASSED\n")


def test_chunking_keeps_tables_whole():
    """Table chunks must never be split."""
    print("=== Test: Table chunks are never split ===")
    service = PDFService(parent_chunk_size=100, parent_chunk_overlap=20)

    pages = [{
        "page_number": 9,
        "elements": [
            (0, "text", "Some intro text."),
            (50, "table", "Row 1 — G3: Matter; G4: Matter.\nRow 2 — G3: Living Things; G4: Living Things."),
            (200, "text", "Some conclusion text."),
        ]
    }]

    chunks = service.chunk_hierarchical(pages)
    table_chunks = [c for c in chunks if c["metadata"]["content_type"] == "table"]
    assert len(table_chunks) == 1
    assert "Row 1" in table_chunks[0]["content"]
    assert "Row 2" in table_chunks[0]["content"]
    print("PASSED\n")


if __name__ == "__main__":
    test_sentence_conversion()
    test_chunking_keeps_tables_whole()
    print("All verification tests PASSED!")
