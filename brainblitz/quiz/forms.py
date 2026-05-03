from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Choice, Question


class QuestionSubmitForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["category", "text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 4}),
        }


class BaseChoiceFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        non_deleted = [
            form
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if len(non_deleted) < 2:
            raise forms.ValidationError("Please provide at least 2 answer choices.")

        correct_count = sum(
            1 for form in non_deleted if form.cleaned_data.get("is_correct") is True
        )
        if correct_count != 1:
            raise forms.ValidationError("Please mark exactly 1 choice as correct.")


ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    fields=["text", "is_correct"],
    extra=4,
    can_delete=False,
    formset=BaseChoiceFormSet,
    widgets={"text": forms.TextInput(attrs={"placeholder": "Choice text"})},
)

