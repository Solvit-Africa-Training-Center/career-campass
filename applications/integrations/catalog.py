import httpx
from django.conf import settings

class CatalogError(Exception):
    """Generic Catalog failure (5xx, 4xx other than 404)."""
    pass

class CatalogNotFound(CatalogError):
    """Program (or route) not found in catalog"""
    pass
def _client() -> httpx.Client:
    """
    A short-lived client per call. for high-throughput, you could promote a module-level, but this keeps it simple and safe
    """
    return httpx.Client(timeout=settings.HTTP_CLIENT_TIMEOUT)

def get_program_required_documents(program_id: str) -> list[dict]:
    """
    Ask Catalog for program-specific required docs.
    Expected 200 JSON:
      [
        {"doc_type_id":"<uuid>","is_mandatory":true,"min_items":1,"max_items":1},
        ...
      ]
    404 -> program not found (we surface CatalogNotFound)
    Other 4xx/5xx -> CatalogError
    """
    url = f"{settings.CATALOG_BASE_URLS}/programs/{program_id}/required-documents"
    with _client() as c:
        r = c.get(url)
    if r.status_code == 404:
        raise CatalogNotFound("program not found")
    if r.is_error:
        # include status code and small slice of the body for debugging
        raise CatalogError(f"Catalog error {r.status_code}: {r.text[:200]}")
    return list(r.json())

def resolve_student_required_documents(student_id: str) -> list[dict]:
    """
    Ask Catalog for student-level baseline requirements (if any).
    Expected 200 JSON shape same as above.
    If resolver returns 404, treat it as “no extra rules” (return []).
    Other errors -> CatalogError (caller can decide to ignore).
    """
    url = f"{settings.CATALOG_BASE_URLS}/student-required-documents:resolve"
    with _client() as c:
        r = c.get(url, params={"student_id": student_id})
    if r.status_code == 404:
        return []
    if r.is_error:
        raise CatalogError(f"Catalog Error {r.status_code}: {r.text[:200]}")
    return list(r.json())