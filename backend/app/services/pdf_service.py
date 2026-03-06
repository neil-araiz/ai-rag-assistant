import fitz  # PyMuPDF
from typing import List, Dict, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter


class PDFService:
    def __init__(self, parent_chunk_size: int = 1200, parent_chunk_overlap: int = 200):
        # Parent splitter — for TEXT blocks only (tables are kept whole)
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_chunk_size,
            chunk_overlap=parent_chunk_overlap,
            length_function=len,
        )
        # Child splitter — for retrieval-optimized small chunks
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
            length_function=len,
        )

    # ------------------------------------------------------------------ #
    #  TABLE → SENTENCE CONVERTER
    # ------------------------------------------------------------------ #

    def _table_to_sentences(self, table) -> str:
        """
        Convert a PyMuPDF Table object into natural-language sentences.
        Each row becomes a descriptive sentence using the column headers.
        Handles merged cells and None values gracefully.
        """
        extracted = table.extract()  # List[List[str | None]]

        if not extracted or len(extracted) < 2:
            # Table has no data rows, return raw text
            return self._table_to_flat_text(extracted)

        # First row = headers
        headers = [str(h).strip() if h else f"Column {i+1}" for i, h in enumerate(extracted[0])]

        sentences = []
        for row_idx, row in enumerate(extracted[1:], start=1):
            parts = []
            for col_idx, cell in enumerate(row):
                if cell is None or str(cell).strip() == "":
                    continue
                cell_text = str(cell).strip()
                header = headers[col_idx] if col_idx < len(headers) else f"Column {col_idx+1}"
                parts.append(f"{header}: {cell_text}")

            if parts:
                sentence = "Row " + str(row_idx) + " — " + "; ".join(parts) + "."
                sentences.append(sentence)

        if not sentences:
            return self._table_to_flat_text(extracted)

        return "\n".join(sentences)

    def _table_to_flat_text(self, extracted: List[List]) -> str:
        """Fallback: join all cell values as plain text."""
        parts = []
        for row in extracted:
            for cell in row:
                if cell and str(cell).strip():
                    parts.append(str(cell).strip())
        return " | ".join(parts)

    # ------------------------------------------------------------------ #
    #  STEP 1 — Layout-Aware Extraction
    # ------------------------------------------------------------------ #

    def extract_text_with_layout(self, file_path: str) -> List[Dict]:
        """
        Extracts structured content from a PDF using PyMuPDF's native
        find_tables() for table detection (no Camelot/Ghostscript needed).
        Returns a list of pages with ordered elements (text or table).
        """
        doc = fitz.open(file_path)
        pages_content = []

        for page_idx, page in enumerate(doc):
            real_page = page_idx + 1

            # --- Detect tables using PyMuPDF native API ---
            table_finder = page.find_tables()
            table_rects = []  # Store bounding boxes to exclude from text blocks
            table_elements = []  # (y_pos, "table", content)

            for table in table_finder.tables:
                bbox = table.bbox  # (x0, y0, x1, y1) in PyMuPDF coords
                table_rects.append(fitz.Rect(bbox))
                sentence_text = self._table_to_sentences(table)
                table_elements.append((bbox[1], "table", sentence_text))

            # --- Extract text blocks, skipping those inside table areas ---
            blocks = page.get_text("blocks")
            elements: List[Tuple[float, str, str]] = []

            for b in blocks:
                bx0, by0, bx1, by1 = b[:4]
                text = b[4].strip()
                if not text:
                    continue

                block_rect = fitz.Rect(bx0, by0, bx1, by1)

                # Skip if this block overlaps with any detected table area
                if any(block_rect.intersects(tr) for tr in table_rects):
                    continue

                # Simple header heuristic
                if len(text) < 100 and not text.endswith(('.', '!', '?', ':')):
                    elements.append((by0, "text", f"## {text}"))
                else:
                    elements.append((by0, "text", text))

            # Merge text and table elements, sort by vertical position
            elements.extend(table_elements)
            elements.sort(key=lambda e: e[0])

            pages_content.append({
                "page_number": real_page,
                "elements": elements
            })

        doc.close()
        return pages_content

    # ------------------------------------------------------------------ #
    #  STEP 2 — Hierarchical Chunking (table-aware)
    # ------------------------------------------------------------------ #

    def chunk_hierarchical(self, pages_content: List[Dict]) -> List[Dict]:
        """
        Chunks content with Parent-Child hierarchy.

        Tables are NEVER split — each table becomes its own parent chunk.
        Text blocks are split into parent (~1200 chars) → child (~300 chars).
        """
        hierarchical_chunks = []

        for page in pages_content:
            page_number = page["page_number"]
            elements = page["elements"]

            text_buffer = []
            parent_index = 0

            def _flush_text_buffer():
                """Process accumulated text blocks as parent/child chunks."""
                nonlocal parent_index
                if not text_buffer:
                    return

                combined_text = "\n\n".join(text_buffer)
                parent_texts = self.parent_splitter.split_text(combined_text)

                for p_text in parent_texts:
                    parent_id = f"p{page_number}_{parent_index}"
                    child_texts = self.child_splitter.split_text(p_text)

                    for c_text in child_texts:
                        hierarchical_chunks.append({
                            "content": c_text,
                            "metadata": {
                                "page_number": page_number,
                                "parent_id": parent_id,
                                "parent_content": p_text,
                                "content_type": "text",
                                "is_child": True,
                            }
                        })
                    parent_index += 1

                text_buffer.clear()

            for _, elem_type, content in elements:
                if elem_type == "table":
                    # Flush any text that came before this table
                    _flush_text_buffer()

                    # Table is its OWN parent — never split
                    parent_id = f"p{page_number}_{parent_index}"
                    table_content = f"[TABLE]\n{content}"

                    hierarchical_chunks.append({
                        "content": table_content,
                        "metadata": {
                            "page_number": page_number,
                            "parent_id": parent_id,
                            "parent_content": table_content,
                            "content_type": "table",
                            "is_child": True,
                        }
                    })
                    parent_index += 1
                else:
                    text_buffer.append(content)

            # Flush remaining text after last element
            _flush_text_buffer()

        return hierarchical_chunks
