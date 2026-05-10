from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q
from accounts.admin import admin_site
from .models import UserImage, AntAnnotation


class LargeImageFilter(admin.SimpleListFilter):
    title = "> 1280px"
    parameter_name = "large"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Oui"),
            ("no", "Non"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(Q(width__gt=1280) | Q(height__gt=1280))
        if self.value() == "no":
            return queryset.exclude(Q(width__gt=1280) | Q(height__gt=1280))
        return queryset


class AntAnnotationInline(admin.TabularInline):
    model = AntAnnotation
    extra = 0
    fields = ("label", "x", "y")
    readonly_fields = ("label", "x", "y")


@admin.register(UserImage, site=admin_site)
class UserImageAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "species", "image_preview", "width", "height", "large_image", "annotation_count", "uploaded_at")
    list_filter = ("species", "uploaded_at", "user", LargeImageFilter)
    search_fields = ("title", "species", "user__email", "user__username")
    readonly_fields = ("width", "height", "uploaded_at", "image_preview")
    inlines = [AntAnnotationInline]
    date_hierarchy = "uploaded_at"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="80" height="60" style="object-fit:cover;border-radius:4px;">',
                obj.image.url,
            )
        return "-"
    image_preview.short_description = "Aperçu"

    def large_image(self, obj):
        if obj.width > 1280 or obj.height > 1280:
            return format_html(
                '<span style="color:#fff;background:#28a745;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold;">{}x{}</span>',
                obj.width, obj.height,
            )
        return format_html(
            '<span style="color:#fff;background:#dc3545;padding:2px 8px;border-radius:10px;font-size:11px;">{}x{}</span>',
            obj.width, obj.height,
        )
    large_image.short_description = "> 1280px"

    def annotation_count(self, obj):
        return obj.annotations.count()
    annotation_count.short_description = "Annotations"


@admin.register(AntAnnotation, site=admin_site)
class AntAnnotationAdmin(admin.ModelAdmin):
    list_display = ("id", "image", "label", "x", "y", "created_at")
    list_filter = ("created_at",)
    search_fields = ("image__title", "image__user__email")
