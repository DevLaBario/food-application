from django.db import models
from tinymce.models import HTMLField


# Create your models here.
class Item(models.Model):
    item_name = models.CharField(max_length=100)
    item_description = models.CharField(
        max_length=200, default="No description available", blank=True
    )  # Changed to CharField for short description
    item_recipe = HTMLField(
        default="<p>Recipe coming soon!</p>", blank=True
    )  # New field for full recipe with rich text
    item_price = models.IntegerField()
    item_image = models.CharField(
        max_length=500,
        default="https://theme-assets.getbento.com/sensei/cb0fd97.sensei/assets/images/catering-item-placeholder-704x520.png",
    )

    def __str__(self):
        return self.item_name


class MealPlan(models.Model):
    """
    Represents a saved meal plan.

    Fields:
    - name: A user-friendly name for the meal plan
    - created_at: When the meal plan was created
    - notes: Optional notes about the meal plan
    """

    name = models.CharField(max_length=200, default="My Meal Plan")
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%B %d, %Y')}"

    class Meta:
        ordering = ["-created_at"]  # Most recent first


class MealPlanDay(models.Model):
    """
    Represents a single day in a meal plan.

    Fields:
    - meal_plan: The meal plan this day belongs to (ForeignKey)
    - day_of_week: Which day (Monday, Tuesday, etc.)
    - recipe: The recipe assigned to this day (ForeignKey)
    - order: The order of the day (0-6 for Mon-Sun)
    """

    meal_plan = models.ForeignKey(
        MealPlan,
        on_delete=models.CASCADE,  # If meal plan is deleted, delete all its days
        related_name="days",  # Allows us to access days via meal_plan.days.all()
    )
    day_of_week = models.CharField(max_length=20)
    recipe = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,  # If recipe is deleted, keep the day but set recipe to NULL
        null=True,
        blank=True,
    )
    order = models.IntegerField(default=0)

    def __str__(self):
        recipe_name = self.recipe.item_name if self.recipe else "No recipe"
        return f"{self.day_of_week}: {recipe_name}"

    class Meta:
        ordering = ["order"]  # Order by the order field
        unique_together = [
            "meal_plan",
            "day_of_week",
        ]  # Each day should appear once per meal plan


class ShoppingList(models.Model):
    """
    Represents a shopping list generated from a meal plan.

    Fields:
    - meal_plan: The meal plan this shopping list is based on (ForeignKey)
    - created_at: When the shopping list was created
    - ingredients: A text field storing the compiled list of ingredients
    """

    meal_plan = models.OneToOneField(
        MealPlan,
        on_delete=models.CASCADE,  # If meal plan is deleted, delete the shopping list
        related_name="shopping_list",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    ingredients = models.TextField(
        blank=True, help_text="Compiled list of ingredients from all recipes"
    )

    def __str__(self):
        return f"Shopping List for {self.meal_plan.name}"

    class Meta:
        ordering = ["-created_at"]
