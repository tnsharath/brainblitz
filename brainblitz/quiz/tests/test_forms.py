from django.test import TestCase

from quiz.forms import ChoiceFormSet
from quiz.models import Category, Question


class ChoiceFormSetTests(TestCase):
    def test_requires_at_least_two_choices(self):
        cat = Category.objects.create(name="C")
        q = Question.objects.create(category=cat, text="Q?", is_approved=False)
        data = {
            "choices-TOTAL_FORMS": "4",
            "choices-INITIAL_FORMS": "0",
            "choices-MIN_NUM_FORMS": "0",
            "choices-MAX_NUM_FORMS": "1000",
            "choices-0-text": "Only one",
            "choices-0-is_correct": "on",
            "choices-1-text": "",
            "choices-2-text": "",
            "choices-3-text": "",
        }
        formset = ChoiceFormSet(data=data, instance=q)
        self.assertFalse(formset.is_valid())
        self.assertTrue(any("at least 2" in e for e in formset.non_form_errors()))

    def test_requires_exactly_one_correct(self):
        cat = Category.objects.create(name="C")
        q = Question.objects.create(category=cat, text="Q?", is_approved=False)
        data = {
            "choices-TOTAL_FORMS": "4",
            "choices-INITIAL_FORMS": "0",
            "choices-MIN_NUM_FORMS": "0",
            "choices-MAX_NUM_FORMS": "1000",
            "choices-0-text": "A",
            "choices-0-is_correct": "on",
            "choices-1-text": "B",
            "choices-1-is_correct": "on",
            "choices-2-text": "C",
            "choices-3-text": "D",
        }
        formset = ChoiceFormSet(data=data, instance=q)
        self.assertFalse(formset.is_valid())
        self.assertTrue(any("exactly 1" in e.lower() for e in formset.non_form_errors()))
