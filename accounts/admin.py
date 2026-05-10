from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin


class SuperuserAdminSite(AdminSite):
    site_header = "AntCounter - Administration"
    site_title = "AntCounter Admin"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser


admin_site = SuperuserAdminSite(name="superadmin")
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
