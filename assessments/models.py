import uuid
from django.db import models
from django.conf import settings

# Represents a whole quiz or survey.
class Assessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    version = models.CharField(max_length=20, default="1.0")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (v{self.version})"

# Represents a single question within an assessment.
class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('interest', 'Interest'),
        ('strength', 'Strength'),
        ('personality', 'Personality'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.text

# Represents a pre-defined answer for a question.
class Choice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255)
    # The 'value' can be used for tagging and scoring in the recommendation engine.
    value = models.CharField(max_length=100, help_text="Internal value/tag for this choice")

    def __str__(self):
        return self.text

# A record that a specific student has taken a specific assessment.
class StudentAssessment(models.Model):
    STATUS_CHOICES = [
        ('not-started', 'Not Started'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_id = models.UUIDField(db_index=True, help_text="UUID reference to a student in the accounts service")
    assessment = models.ForeignKey(Assessment, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not-started')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student_id', 'assessment')

    def __str__(self):
        return f"Assessment for student {self.student_id} - {self.assessment.title}"

# Stores the actual answer a student gave for a question.
class StudentAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_assessment = models.ForeignKey(StudentAssessment, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    chosen_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('student_assessment', 'question')

    def __str__(self):
        return f"Answer for {self.student_assessment.student_id} to '{self.question.text}'"
