from django.contrib import admin
from django.db.models import Exists, OuterRef

from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class TagUsageFilter(admin.SimpleListFilter):
    title = 'использование'
    parameter_name = 'usage'

    def lookups(self, request, model_admin):
        return [('used', 'Есть вопросы'), ('unused', 'Нет вопросов')]

    def queryset(self, request, queryset):
        links = Question.tags.through.objects.filter(tag_id=OuterRef('pk'))
        if self.value() == 'used':
            return queryset.filter(Exists(links))
        if self.value() == 'unused':
            return queryset.filter(~Exists(links))
        return queryset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = (TagUsageFilter,)
    show_full_result_count = False


class AnswerInline(admin.TabularInline):
    model = Answer
    fields = ('author', 'text', 'created', 'is_correct')
    readonly_fields = fields
    show_change_link = True
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created')
    list_select_related = ('author',)
    search_fields = ('title', 'text', 'author__username')
    list_filter = ('created',)
    raw_id_fields = ('author',)
    autocomplete_fields = ('tags',)
    inlines = (AnswerInline,)
    show_full_result_count = False


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'author', 'is_correct', 'created')
    list_select_related = ('question', 'author')
    search_fields = ('text', 'question__title', 'author__username')
    list_filter = ('is_correct', 'created')
    raw_id_fields = ('question', 'author')
    show_full_result_count = False


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ('question', 'user', 'value')
    list_select_related = ('question', 'user')
    search_fields = ('question__title', 'user__username')
    list_filter = ('value',)
    raw_id_fields = ('question', 'user')
    show_full_result_count = False


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ('answer', 'user', 'value')
    list_select_related = ('answer', 'user')
    search_fields = ('answer__text', 'user__username')
    list_filter = ('value',)
    raw_id_fields = ('answer', 'user')
    show_full_result_count = False
