# Generated manually for MongoDB analytics integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0002_attemptanswer_unique_answer_per_question_per_attempt_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="quizattempt",
            name="mongo_log_id",
            field=models.CharField(blank=True, max_length=24),
        ),
    ]
