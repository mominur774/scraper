from django.contrib import admin
from scrap.models import User

# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'password', 'used', )

admin.site.register(User, UserAdmin)