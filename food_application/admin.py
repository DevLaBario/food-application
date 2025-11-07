from django.contrib import admin
from .models import Item, MealPlan, MealPlanDay, ShoppingList


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


# Custom admin for ShoppingList
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ["meal_plan", "created_at", "get_ingredient_count"]
    list_filter = ["created_at"]
    search_fields = ["meal_plan__name", "ingredients"]
    readonly_fields = ["created_at"]

    def get_ingredient_count(self, obj):
        if obj.ingredients:
            return len(obj.ingredients.split("\n"))
        return 0

    get_ingredient_count.short_description = "Number of Ingredients"


# Register your models here.
admin.site.register(Item)
admin.site.register(MealPlan, MealPlanAdmin)
admin.site.register(MealPlanDay)
admin.site.register(ShoppingList, ShoppingListAdmin)
