import httpx
from django.conf import settings

class DocumentsError(Exception):
    pass

class StudentDocumentNotFound(DocumentsError):
    pass

def _client() -> httpx.Client:
    return httpx.Client(timeout=settings.HTTP_CLIENT_TIMEOUT)

def get_student_document(doc_id: str) -> dict:
    """
    Expect 200 JSON:
      {"id":"<uuid>","user_id":"<uuid>","doc_type_id":"<uuid>","status":"pending|clean|infected"}
    """
    url = f"{settings.DOCUMENTS_BASE_URL}/student-documents/{doc_id}/"
    with _client() as c:
        r = c.get(url)
    if r.status_code == 404:
        raise StudentDocumentNotFound("student document not found")
    if r.is_error:
        raise DocumentsError(f"Documents error {r.status_code}: {r.text[:200]}")
    return dict(r.json())
