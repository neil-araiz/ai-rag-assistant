import fitz  # PyMuPDF
import camelot
import os
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
    #  STEP 1 — Layout-Aware Extraction
    # ------------------------------------------------------------------ #

    def extract_text_with_layout(self, file_path: str) -> List[Dict]:
        """
        Extracts structured content from a PDF.
        Returns a list of pages, each containing ordered 'elements' that are
        either TEXT blocks or TABLE blocks (never duplicated).
        """
        doc = fitz.open(file_path)

        # --- Camelot table extraction (get table bounding boxes per page) ---
        tables_by_page: Dict[int, List[Dict]] = {}
        try:
            camelot_tables = camelot.read_pdf(file_path, pages='all', flavor='stream')
            for table in camelot_tables:
                page_num = table.page  # 1-indexed
                if page_num not in tables_by_page:
                    tables_by_page[page_num] = []
                # Store markdown + bounding box for dedup
                md_table = table.df.to_markdown(index=False)
                # Camelot bbox: (x0, y0, x1, y1) — PDF coordinates
                bbox = table._bbox if hasattr(table, '_bbox') else None
                tables_by_page[page_num].append({
                    "markdown": md_table,
                    "bbox": bbox
                })
        except Exception as e:
            print(f"Camelot table extraction skipped: {e}")

        # --- Per-page: merge text blocks + tables in reading order ---
        pages_content = []
        for page_idx, page in enumerate(doc):
            real_page = page_idx + 1
            page_height = page.rect.height

            # Get all text blocks from PyMuPDF
            blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)

            # Build a set of table regions so we can skip text blocks inside them
            table_regions = []
            if real_page in tables_by_page:
                for tbl_info in tables_by_page[real_page]:
                    if tbl_info["bbox"]:
                        # Camelot uses PDF coords (origin bottom-left)
                        # Convert to PyMuPDF coords (origin top-left)
                        bx0, by0, bx1, by1 = tbl_info["bbox"]
                        table_regions.append(fitz.Rect(bx0, page_height - by1, bx1, page_height - by0))

            # Collect elements with their y-position for ordering
            elements: List[Tuple[float, str, str]] = []  # (y_pos, type, content)

            # Add text blocks (skip those overlapping table regions)
            for b in blocks:
                bx0, by0, bx1, by1 = b[:4]
                text = b[4].strip()
                if not text:
                    continue

                block_rect = fitz.Rect(bx0, by0, bx1, by1)

                # Skip if this block overlaps with any detected table area
                if any(block_rect.intersects(tr) for tr in table_regions):
                    continue

                # Simple header heuristic
                if len(text) < 100 and not text.endswith(('.', '!', '?', ':')):
                    elements.append((by0, "text", f"## {text}"))
                else:
                    elements.append((by0, "text", text))

            # Add table elements at their approximate y-position
            if real_page in tables_by_page:
                for tbl_info in tables_by_page[real_page]:
                    y_pos = 0
                    if tbl_info["bbox"]:
                        y_pos = page_height - tbl_info["bbox"][3]  # top of table
                    elements.append((y_pos, "table", tbl_info["markdown"]))

            # Sort by vertical position (reading order)
            elements.sort(key=lambda e: e[0])

            pages_content.append({
                "page_number": real_page,
                "elements": elements  # [(y, type, content), ...]
            })

        doc.close()
        return pages_content

    # ------------------------------------------------------------------ #
    #  STEP 2 — Hierarchical Chunking (table-aware)
    # ------------------------------------------------------------------ #

    def chunk_hierarchical(self, pages_content: List[Dict]) -> List[Dict]:
        """
        Chunks content with Parent-Child hierarchy.
        
        KEY FIX: Tables are NEVER split by the text splitter.
        Instead, each table becomes its own parent chunk.
        Only regular text blocks are split into parent/child pairs.
        """
        hierarchical_chunks = []

        for page in pages_content:
            page_number = page["page_number"]
            elements = page["elements"]

            # Separate elements into contiguous text runs and standalone tables
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

                    # For tables, child == parent (no splitting)
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
