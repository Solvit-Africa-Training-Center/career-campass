import httpx
from django.conf import settings
from core.utils.uuid_helpers import is_valid_uuid

class DocumentsError(Exception):
    """Base exception for document service errors."""
    pass

class StudentDocumentNotFound(DocumentsError):
    """Exception raised when a student document is not found."""
    pass

class InvalidDocumentIdError(DocumentsError):
    """Exception raised when an invalid document ID is provided."""
    pass

def _client() -> httpx.Client:
    """Create a new HTTP client with timeout setting."""
    return httpx.Client(timeout=settings.HTTP_CLIENT_TIMEOUT)

def get_student_document(doc_id: str) -> dict:
    """
    Retrieve a student document by ID.
    
    Args:
        doc_id: UUID string of the document
        
    Returns:
        dict: Document data in the format:
            {"id":"<uuid>","user_id":"<uuid>","doc_type_id":"<uuid>","status":"pending|clean|infected"}
            
    Raises:
        InvalidDocumentIdError: If doc_id is not a valid UUID
        StudentDocumentNotFound: If document not found (HTTP 404)
        DocumentsError: For other HTTP errors
    """
    # Validate UUID before making request
    if not is_valid_uuid(doc_id):
        raise InvalidDocumentIdError(f"Invalid document ID format: {doc_id}")
        
    url = f"{settings.DOCUMENTS_BASE_URL}/student-documents/{doc_id}/"
    
    try:
        with _client() as c:
            r = c.get(url)
            
        if r.status_code == 404:
            raise StudentDocumentNotFound(f"Student document not found: {doc_id}")
            
        if r.is_error:
            raise DocumentsError(f"Documents service error {r.status_code}: {r.text[:200]}")
            
        return dict(r.json())
        
    except httpx.RequestError as e:
        raise DocumentsError(f"Network error when contacting documents service: {str(e)}")
    except httpx.TimeoutException:
        raise DocumentsError("Timeout while contacting documents service")
