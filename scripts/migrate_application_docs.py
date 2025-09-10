import os
import sys
import django
from django.db import transaction
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Import models after Django setup
from documents.models import ApplicationDocument as NewApplicationDocument
from documents.models import UserDocument, DocumentType, ProgramDocument
from applications.models import Application

# Helper function to migrate application documents
def migrate_application_documents():
    """
    Migrate data from the old ApplicationDocument model in applications app
    to the new consolidated ApplicationDocument model in documents app.
    
    This script should be run after making the model changes but before
    removing the old model from applications/models.py.
    """
    from applications.models import ApplicationDocument as OldApplicationDocument
    
    print(f"Found {OldApplicationDocument.objects.count()} records to migrate")
    
    migrated = 0
    errors = 0
    
    for old_doc in OldApplicationDocument.objects.all():
        try:
            # Get the application
            app = Application.objects.get(id=old_doc.application.id)
            
            # Get the document type
            doc_type = DocumentType.objects.get(id=old_doc.doc_type_id)
            
            # Try to get the user document
            try:
                user_doc = UserDocument.objects.get(id=old_doc.student_document_id)
            except UserDocument.DoesNotExist:
                print(f"Warning: UserDocument {old_doc.student_document_id} not found. Creating placeholder...")
                # Create a placeholder with minimal data
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(id=app.student_id)
                user_doc = UserDocument.objects.create(
                    id=old_doc.student_document_id,
                    user=user,
                    document_type=doc_type,
                    issued_date=app.created_at,
                    expires_date=app.created_at + timezone.timedelta(days=365)
                )
            
            # Try to get the program document
            try:
                program_doc = ProgramDocument.objects.get(
                    program_id=app.program_id,
                    document_type=doc_type
                )
            except ProgramDocument.DoesNotExist:
                print(f"Warning: ProgramDocument for program {app.program_id} and doc_type {doc_type.id} not found. Creating...")
                # Create a placeholder
                from catalog.models import Program
                program = Program.objects.get(id=app.program_id)
                program_doc = ProgramDocument.objects.create(
                    program=program,
                    document_type=doc_type,
                    is_mandatory=True
                )
            
            # Create the new application document
            with transaction.atomic():
                NewApplicationDocument.objects.create(
                    id=old_doc.id,  # Keep the same ID
                    user_document=user_doc,
                    program_document=program_doc,
                    is_verified=True,
                    application=app.id,
                    doc_type_id=old_doc.doc_type_id,
                    student_document_id=old_doc.student_document_id,
                    created_at=old_doc.created_at
                )
                migrated += 1
        except Exception as e:
            print(f"Error migrating document {old_doc.id}: {e}")
            errors += 1
    
    print(f"Migration complete. Migrated: {migrated}, Errors: {errors}")

if __name__ == "__main__":
    migrate_application_documents()
