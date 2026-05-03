from django import forms
from django.contrib import admin
from django.forms.models import BaseInlineFormSet

from .models import Category, Choice, Question, Quiz, QuizAttempt, QuizQuestion, UserProfile


class ChoiceInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(f.errors for f in self.forms):
            return

        non_deleted = [
            f
            for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get("DELETE", False)
        ]
        filled = [
            f
            for f in non_deleted
            if (f.cleaned_data.get("text") or "").strip()
        ]
        if len(filled) < 2:
            raise forms.ValidationError(
                "Add at least 2 answer choices with text."
            )

        correct_count = sum(
            1 for f in filled if f.cleaned_data.get("is_correct") is True
        )
        if correct_count != 1:
            raise forms.ValidationError(
                "Mark exactly one choice as the correct answer."
            )


class ChoiceInline(admin.TabularInline):
    model = Choice
    formset = ChoiceInlineFormSet
    fields = ("text", "is_correct")
    extra = 3
    min_num = 2
    verbose_name = "Answer choice"
    verbose_name_plural = "Answer choices"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fields = ["category", "text", "is_approved", "created_by"]
    list_display = ["text", "category", "created_by", "is_approved"]
    list_filter = ["is_approved", "category"]
    search_fields = ["text"]
    inlines = [ChoiceInline]
    actions = ["approve_selected_questions"]

    def save_model(self, request, obj, form, change):
        if not change and obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Approve selected questions")
    def approve_selected_questions(self, request, queryset):
        queryset.update(is_approved=True)


admin.site.register(Category)
admin.site.register(Quiz)
admin.site.register(QuizQuestion)
admin.site.register(QuizAttempt)
admin.site.register(UserProfile)
