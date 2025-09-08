from typing import Iterable, Dict, List, TypedDict, Optional
import logging
from core.utils.uuid_helpers import is_valid_uuid

logger = logging.getLogger(__name__)

class RequiredDocument(TypedDict, total=False):
    """Type definition for a required document."""
    doc_type_id: str
    is_mandatory: bool
    min_items: int
    max_items: int
    source: str

def validate_document_req(doc: Dict) -> Optional[Dict]:
    """
    Validate a document requirement entry.
    
    Args:
        doc: Document requirement dictionary
        
    Returns:
        Optional[Dict]: Validated document or None if invalid
    """
    if "doc_type_id" not in doc:
        logger.warning("Document requirement missing doc_type_id field")
        return None
        
    # Validate UUID
    if not is_valid_uuid(doc["doc_type_id"]):
        logger.warning(f"Invalid UUID in doc_type_id: {doc['doc_type_id']}")
        return None
    
    return doc

def merge_required_docs(program_reqs: Iterable[Dict], student_reqs: Iterable[Dict]) -> List[RequiredDocument]:
    """
    Merge program and student document requirements by doc_type_id.
    
    When both sides specify the same doc_type_id:
      - is_mandatory: OR (if either requires it, it's required)
      - min_items: max() (stricter wins)
      - max_items: max() (stricter wins)
      - source: 'program' if present, else 'student' (informational)
    
    Args:
        program_reqs: Program document requirements
        student_reqs: Student document requirements
        
    Returns:
        List[RequiredDocument]: Merged requirements in the format:
            { "doc_type_id": "<uuid>", "is_mandatory": bool, "min_items": int, "max_items": int, "source": "program|student" }
    """
    by_id: Dict[str, RequiredDocument] = {}
    
    def upsert(items: Iterable[Dict], source: str):
        for it in items:
            # Validate document requirement
            valid_doc = validate_document_req(it)
            if valid_doc is None:
                continue
                
            dt = str(valid_doc["doc_type_id"])
            is_mand = bool(valid_doc.get("is_mandatory", True))
            min_i = int(valid_doc.get("min_items", 1))
            max_i = int(valid_doc.get("max_items", 1))
            
            if dt in by_id:
                prev = by_id[dt]
                prev["is_mandatory"] = prev["is_mandatory"] or is_mand
                prev["min_items"] = max(prev["min_items"], min_i)
                prev["max_items"] = max(prev["max_items"], max_i)
                
                # Program source takes precedence
                if prev["source"] != "program" and source == "program":
                    prev["source"] = "program"
            else:
                by_id[dt] = {
                    "doc_type_id": dt,
                    "is_mandatory": is_mand,
                    "min_items": min_i,
                    "max_items": max_i,
                    "source": source,
                }
    
    # Process program requirements first (they take precedence)
    upsert(program_reqs, "program")
    upsert(student_reqs, "student")
    
    logger.debug(f"Merged {len(by_id)} document requirements")
    return list(by_id.values())