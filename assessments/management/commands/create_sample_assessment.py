from django.core.management.base import BaseCommand
from assessments.models import Assessment, Question, Choice
import uuid

class Command(BaseCommand):
    help = 'Creates a sample assessment with questions and choices.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample assessment...')

        # Create the main assessment
        assessment, created = Assessment.objects.get_or_create(
            title="Career Interest & Personality Quiz",
            defaults={'version': '1.0', 'description': 'A short quiz to help you discover your career interests and personality traits.'}
        )

        if not created:
            self.stdout.write(self.style.WARNING('Assessment already exists. Skipping creation.'))
            return

        # --- Question 1: Interest ---
        q1 = Question.objects.create(
            assessment=assessment,
            text="Which of these activities sounds most enjoyable to you?",
            question_type='interest',
            display_order=1
        )
        Choice.objects.create(question=q1, text="Building a robot or a piece of software", value="technology")
        Choice.objects.create(question=q1, text="Conducting a scientific experiment", value="science")
        Choice.objects.create(question=q1, text="Designing a logo or a piece of art", value="creative")
        Choice.objects.create(question=q1, text="Helping someone solve a personal problem", value="social")

        # --- Question 2: Strength ---
        q2 = Question.objects.create(
            assessment=assessment,
            text="What are you best at?",
            question_type='strength',
            display_order=2
        )
        Choice.objects.create(question=q2, text="Solving complex math or logic puzzles", value="analytical")
        Choice.objects.create(question=q2, text="Leading a team to achieve a goal", value="leadership")
        Choice.objects.create(question=q2, text="Organizing projects and paying attention to details", value="organization")
        Choice.objects.create(question=q2, text="Coming up with new, unconventional ideas", value="innovative")

        # --- Question 3: Personality ---
        q3 = Question.objects.create(
            assessment=assessment,
            text="In a group project, you prefer to:",
            question_type='personality',
            display_order=3
        )
        Choice.objects.create(question=q3, text="Work independently on your assigned part", value="independent")
        Choice.objects.create(question=q3, text="Collaborate closely with others and brainstorm together", value="collaborative")
        Choice.objects.create(question=q3, text="Take charge and delegate tasks", value="leader")
        Choice.objects.create(question=q3, text="Focus on the research and data analysis", value="analytical")

        self.stdout.write(self.style.SUCCESS('Successfully created sample assessment.'))
