from typing import Iterable, Dict, List, TypedDict

def merge_required_docs(program_reqs: Iterable[Dict], student_reqs: Iterable[Dict]) -> List[Dict]:
    """
    Union by doc_type_id. When both sides specify the same doc_type_id:
      - is_mandatory: OR (if either requires it, it's required)
      - min_items: max()  (stricter wins)
      - max_items: max()
      - source: 'program' if present, else 'student'  (informational)
    Return each item as:
      { "doc_type_id": "<uuid>", "is_mandatory": bool, "min_items": int, "max_items": int, "source": "program|student" }
    """
    by_id: Dict[str, Dict] = {}
    
    def upsert(items: Iterable[Dict], source: str):
        for it in items:
            dt = str(it["doc_type_id"])
            is_mand = bool(it.get("is_mandatory", True))
            min_i = int(it.get("min_items", 1))
            max_i = int(it.get("max_items", 1))
            
            if dt in by_id:
                prev = by_id[dt]
                prev["is_mandatory"] = prev["is_mandatory"] or is_mand
                prev["min_items"] = max(prev["min_items"], min_i)
                prev["max_items"] = max(prev["max_items"], max_i)
                
                if prev["source"] != "program" and source == "program":
                    prev["source"] = "program"
            else:
                by_id[dt] = {
                    "doc_type_id" : dt,
                    "is_mandatory": is_mand,
                    "min_items": min_i,
                    "max_items": max_i,
                    "source": source,
                }
    upsert(program_reqs, "program")
    upsert(student_reqs, "student")
    return list(by_id.values())