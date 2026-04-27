"""Extract text and tables from uploaded DOCX files."""
import io

import structlog

log = structlog.get_logger()


def extract_docx_full(data: bytes) -> str:
    """Extract paragraphs + all table content from a .docx file.
    Tables are serialised as pipe-delimited rows so the LLM can read them.
    """
    from docx import Document

    doc = Document(io.BytesIO(data))
    parts: list[str] = []

    # Iterate document body in order (paragraphs and tables interleaved)
    for block in doc.element.body:
        tag = block.tag.split("}")[-1]  # strip namespace

        if tag == "p":
            # Paragraph
            from docx.oxml.ns import qn
            text = "".join(node.text or "" for node in block.iter() if node.tag == qn("w:t"))
            if text.strip():
                parts.append(text.strip())

        elif tag == "tbl":
            # Table — extract as pipe-delimited rows
            from docx.table import Table
            from docx.oxml.ns import qn as _qn

            rows_text: list[str] = []
            for row in block.findall(".//" + "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr"):
                cells = []
                for cell in row.findall(".//" + "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc"):
                    cell_text = "".join(
                        n.text or ""
                        for n in cell.iter()
                        if n.tag == "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
                    ).strip()
                    cells.append(cell_text)
                if any(cells):
                    rows_text.append(" | ".join(cells))

            if rows_text:
                parts.append("[TABLE]\n" + "\n".join(rows_text) + "\n[/TABLE]")

    result = "\n\n".join(parts)
    log.info("extractor.docx", chars=len(result))
    return result
