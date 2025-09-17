from rest_framework import serializers
from .models import Assessment, Question, Choice, StudentAssessment, StudentAnswer

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'value']

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'display_order', 'choices']

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'title', 'version', 'description']

class StudentAnswerInputSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    choice_id = serializers.UUIDField()

class SubmitAssessmentSerializer(serializers.Serializer):
    answers = StudentAnswerInputSerializer(many=True)
