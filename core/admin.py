from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 1
    max_num = 1
    can_delete = False


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = (ProfileInline,)

    def get_inlines(self, request, obj=None):
        return self.inlines if obj else ()


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nickname', 'rating')
    list_select_related = ('user',)
    search_fields = ('nickname', 'user__username', 'user__email')
    list_filter = ('user__is_active', ('avatar', admin.EmptyFieldListFilter))
    raw_id_fields = ('user',)
    show_full_result_count = False
