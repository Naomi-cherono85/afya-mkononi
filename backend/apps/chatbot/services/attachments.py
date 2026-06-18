"""Attachment handling for multimodal chat.

Two responsibilities, kept out of the view and the Anthropic client:

* ``extract_document_text`` — pull plain text out of an uploaded PDF, DOCX, or
  TXT file so it can be folded into the AI prompt.
* ``image_payload`` — read an uploaded image and return the base64 data + media
  type the Anthropic vision API expects.

Everything is best-effort: extraction failures degrade to an empty string and a
short note rather than breaking the chat flow.
"""

from __future__ import annotations

import base64
import logging

logger = logging.getLogger(__name__)

# Documents longer than this (in characters) are truncated before being sent to
# the model, to keep token usage and latency bounded.
MAX_EXTRACTED_CHARS = 20_000


def _read_txt(file) -> str:
    file.seek(0)
    raw = file.read()
    if isinstance(raw, bytes):
        # Be forgiving about encoding — most clinical/text uploads are UTF-8.
        return raw.decode('utf-8', errors='replace')
    return raw


def _read_pdf(file) -> str:
    from pypdf import PdfReader

    file.seek(0)
    reader = PdfReader(file)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or '')
    return '\n'.join(parts)


def _read_docx(file) -> str:
    import docx

    file.seek(0)
    document = docx.Document(file)
    return '\n'.join(p.text for p in document.paragraphs)


_EXTRACTORS = {
    'txt': _read_txt,
    'pdf': _read_pdf,
    'docx': _read_docx,
}


def extract_document_text(attachment) -> str:
    """Return extracted text for a document attachment ('' on failure/unknown).

    ``attachment`` is a ``ChatAttachment``. The result is whitespace-collapsed
    and truncated to ``MAX_EXTRACTED_CHARS`` so the prompt stays bounded.
    """
    extractor = _EXTRACTORS.get(attachment.extension)
    if not extractor:
        return ''

    try:
        with attachment.file.open('rb') as fh:
            text = extractor(fh)
    except Exception:
        logger.exception('Failed to extract text from attachment %s', attachment.pk)
        return ''

    text = (text or '').strip()
    if len(text) > MAX_EXTRACTED_CHARS:
        text = text[:MAX_EXTRACTED_CHARS].rstrip() + '\n\n[document truncated]'
    return text


def image_payload(attachment) -> dict | None:
    """Return ``{'media_type', 'data'}`` (base64) for an image attachment.

    Returns ``None`` if the file is not a supported image or cannot be read.
    """
    media_type = attachment.media_type
    if not media_type:
        return None
    try:
        with attachment.file.open('rb') as fh:
            data = base64.standard_b64encode(fh.read()).decode('ascii')
    except Exception:
        logger.exception('Failed to read image attachment %s', attachment.pk)
        return None
    return {'media_type': media_type, 'data': data}
