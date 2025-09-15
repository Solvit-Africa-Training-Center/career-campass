from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from .models import Assessment, Question, StudentAssessment, StudentAnswer
from .serializers import AssessmentSerializer, QuestionSerializer, SubmitAssessmentSerializer
from accounts.utils import get_student_uuid

from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Assessments'])
class AssessmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing assessments and their questions.
    """
    queryset = Assessment.objects.filter(is_active=True)
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """
        Return a list of all questions for a given assessment.
        """
        assessment = self.get_object()
        questions = assessment.questions.all().prefetch_related('choices')
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def submit(self, request, pk=None):
        """
        Submit answers for an assessment.
        """
        assessment = get_object_or_404(Assessment, pk=pk)
        student_id = get_student_uuid(request.user)

        if not student_id:
            return Response({"detail": "Only students can submit assessments."}, status=status.HTTP_403_FORBIDDEN)

        serializer = SubmitAssessmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers_data = serializer.validated_data['answers']

        # Create or get the StudentAssessment record
        student_assessment, created = StudentAssessment.objects.get_or_create(
            student_id=student_id,
            assessment=assessment,
            defaults={'status': 'in-progress'}
        )

        if student_assessment.status == 'completed':
            return Response({"detail": "You have already completed this assessment."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate questions belong to the assessment
        question_ids = {answer['question_id'] for answer in answers_data}
        if not all(q.assessment == assessment for q in Question.objects.filter(pk__in=question_ids)):
            return Response({"detail": "One or more questions do not belong to this assessment."}, status=status.HTTP_400_BAD_REQUEST)

        # Create StudentAnswer objects
        for answer_data in answers_data:
            StudentAnswer.objects.update_or_create(
                student_assessment=student_assessment,
                question_id=answer_data['question_id'],
                defaults={'chosen_choice_id': answer_data['choice_id']}
            )

        # Mark assessment as completed
        student_assessment.status = 'completed'
        student_assessment.completed_at = timezone.now()
        student_assessment.save()

        # Here you could trigger the recommendation engine in a background task
        # For now, we just return a success message.

        return Response({"detail": "Assessment submitted successfully."}, status=status.HTTP_200_OK)
