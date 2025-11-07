from django.contrib import admin
from .models import Item, MealPlan, MealPlanDay


# Inline admin for MealPlanDay - shows days within the meal plan edit page
class MealPlanDayInline(admin.TabularInline):
    model = MealPlanDay
    extra = 0  # Don't show extra empty rows
    ordering = ["order"]


# Custom admin for MealPlan
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at", "get_days_count"]
    list_filter = ["created_at"]
    search_fields = ["name", "notes"]
    inlines = [MealPlanDayInline]

    def get_days_count(self, obj):
        return obj.days.count()

    get_days_count.short_description = "Number of Days"


# Register your models here.
admin.site.register(Item)
admin.site.register(MealPlan, MealPlanAdmin)
admin.site.register(MealPlanDay)
