"""
Utility functions to help with document management across the applications and documents apps.
"""
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

def sync_application_document(app_id, doc_type_id, student_document_id) -> bool:
    """
    Synchronizes an ApplicationDocument created in the applications app
    with the ApplicationDocument model in the documents app.
    
    This is a one-way sync: from applications to documents.
    
    Args:
        app_id: UUID of the application
        doc_type_id: UUID of the document type
        student_document_id: UUID of the student document
        
    Returns:
        bool: True if sync was successful, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from applications.models import Application
        from documents.models import UserDocument, DocumentType, ProgramDocument, ApplicationDocument as DocsApplicationDocument
        
        # Get the application
        app = Application.objects.get(id=app_id)
        
        # Get required objects from documents app
        try:
            doc_type = DocumentType.objects.get(id=doc_type_id)
            user_doc = UserDocument.objects.get(id=student_document_id)
            
            # Find or create the program document
            program_doc, created = ProgramDocument.objects.get_or_create(
                program_id=app.program_id,
                document_type=doc_type,
                defaults={'is_mandatory': True}
            )
            
            # Check if a document already exists
            existing = DocsApplicationDocument.objects.filter(
                user_document=user_doc,
                program_document=program_doc
            ).first()
            
            if not existing:
                # Create a new record in documents app
                DocsApplicationDocument.objects.create(
                    user_document=user_doc,
                    program_document=program_doc,
                    is_verified=True  # We assume it's verified if it's attached to an application
                )
                logger.info(f"Created documents.ApplicationDocument for app {app_id}, doc {student_document_id}")
            
            return True
            
        except (DocumentType.DoesNotExist, UserDocument.DoesNotExist) as e:
            logger.warning(f"Could not sync ApplicationDocument: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error syncing ApplicationDocument: {e}")
        return False


def get_document_counts_by_type(application_id) -> Dict[str, int]:
    """
    Get counts of documents attached to an application, grouped by document type.
    
    Args:
        application_id: UUID of the application
        
    Returns:
        Dict mapping document type IDs to counts
    """
    from applications.models import ApplicationDocument
    
    counts = {}
    docs = ApplicationDocument.objects.filter(application_id=application_id)
    
    for doc in docs:
        doc_type_id = str(doc.doc_type_id)
        counts[doc_type_id] = counts.get(doc_type_id, 0) + 1
    
    return counts
