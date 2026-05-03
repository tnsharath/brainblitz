from django.contrib import admin

from .models import Category, Choice, Question, Quiz, QuizAttempt, QuizQuestion, UserProfile


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["text", "category", "created_by", "is_approved"]
    list_filter = ["is_approved", "category"]
    search_fields = ["text"]
    inlines = [ChoiceInline]
    actions = ["approve_selected_questions"]

    @admin.action(description="Approve selected questions")
    def approve_selected_questions(self, request, queryset):
        queryset.update(is_approved=True)


admin.site.register(Category)
admin.site.register(Choice)
admin.site.register(Quiz)
admin.site.register(QuizQuestion)
admin.site.register(QuizAttempt)
admin.site.register(UserProfile)