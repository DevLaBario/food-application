from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q  # Import Q for complex queries
from .models import Item, MealPlan, MealPlanDay, ShoppingList
from .forms import ItemForm
from django.contrib import messages
import re
from bs4 import BeautifulSoup
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy


# Create your views here.


class IndexClassView(LoginRequiredMixin, ListView):
    model = Item
    template_name = "food_application/home/index.html"
    context_object_name = "item_list"
    login_url = "/users/login/"


class RecipeDetailView(DetailView):
    model = Item
    template_name = "food_application/recipes/detail.html"
    context_object_name = "item"
    pk_url_kwarg = "id"


class RecipeCreateView(CreateView):
    model = Item
    form_class = ItemForm
    template_name = "food_application/recipes/item-form.html"
    success_url = reverse_lazy("food_application:index")


class RecipeUpdateView(UpdateView):
    model = Item
    form_class = ItemForm
    template_name = "food_application/recipes/recipe_update.html"
    success_url = reverse_lazy("food_application:index")
    pk_url_kwarg = "id"


class RecipeDeleteView(DeleteView):
    model = Item
    template_name = "food_application/recipes/delete_recipe.html"
    success_url = reverse_lazy("food_application:index")
    pk_url_kwarg = "id"


# Custom Functions Below
def search(request):
    """
    Search view that handles recipe searches.

    How it works:
    1. Gets the 'q' parameter from the URL (e.g., ?q=pizza)
    2. Uses Django's Q objects to search multiple fields at once
    3. The 'icontains' lookup performs case-insensitive partial matching
    4. Returns matching results to the search_results template
    """
    query = request.GET.get(
        "q", ""
    )  # Get search term from URL, default to empty string

    if query:
        # Q objects allow complex database queries with OR conditions
        # icontains = case-insensitive contains
        # __icontains looks for the query anywhere in the field
        results = Item.objects.filter(
            Q(item_name__icontains=query)  # Search in recipe name
            | Q(item_description__icontains=query)  # Search in description
            | Q(item_recipe__icontains=query)  # Search in full recipe
        ).distinct()  # Remove duplicates if a recipe matches multiple fields
    else:
        results = Item.objects.none()  # Empty queryset if no search term

    context = {"results": results, "query": query, "result_count": results.count()}
    return render(request, "food_application/home/search_results.html", context)


def meal_planner(request):
    """
    Generate a weekly meal plan by randomly selecting 7 recipes from the database.
    Each recipe is assigned to a day of the week (Monday through Sunday).
    """
    import random

    # Get all recipes from the database
    all_items = list(Item.objects.all())

    # Check if we have enough recipes
    if len(all_items) < 7:
        # If less than 7 recipes, we can repeat some or show a message
        meal_plan = random.sample(all_items, min(len(all_items), 7))
        # If we have fewer than 7, pad with None or repeat
        while len(meal_plan) < 7:
            meal_plan.append(random.choice(all_items) if all_items else None)
    else:
        # Randomly select 7 recipes
        meal_plan = random.sample(all_items, 7)

    # Create a list of days
    days_of_week = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    # Pair each day with a recipe
    weekly_plan = list(zip(days_of_week, meal_plan))

    context = {"weekly_plan": weekly_plan, "total_recipes": len(all_items)}

    return render(request, "food_application/meal_planning/meal_planner.html", context)


def save_meal_plan(request):
    """
    Save the current meal plan to the database.

    Process:
    1. Receive POST data containing recipe IDs for each day
    2. Create a new MealPlan object
    3. Create MealPlanDay objects for each day/recipe pair
    4. Redirect to the saved meal plans list
    """
    if request.method == "POST":
        # Get the meal plan name from the form (or use default)
        plan_name = request.POST.get("plan_name", "My Meal Plan")

        # Create a new MealPlan
        meal_plan = MealPlan.objects.create(name=plan_name)

        # Days of the week
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        # Loop through each day and save the recipe
        for index, day in enumerate(days):
            recipe_id = request.POST.get(f"recipe_{day}")  # Get recipe ID for this day

            if recipe_id and recipe_id != "None":  # If there's a recipe for this day
                try:
                    recipe = Item.objects.get(id=recipe_id)
                    # Create a MealPlanDay entry
                    MealPlanDay.objects.create(
                        meal_plan=meal_plan, day_of_week=day, recipe=recipe, order=index
                    )
                except Item.DoesNotExist:
                    pass  # Skip if recipe doesn't exist

        # Show success message
        messages.success(request, f"Meal plan '{plan_name}' saved successfully!")
        return redirect("food_application:saved_meal_plans")

    return redirect("food_application:meal_planner")


def saved_meal_plans(request):
    """
    Display a list of all saved meal plans.
    """
    meal_plans = MealPlan.objects.all()
    context = {"meal_plans": meal_plans}
    return render(
        request, "food_application/meal_planning/saved_meal_plans.html", context
    )


def view_meal_plan(request, plan_id):
    """
    View a specific saved meal plan.
    """
    meal_plan = MealPlan.objects.get(id=plan_id)
    # Get all days for this meal plan (automatically ordered by the 'order' field)
    days = meal_plan.days.all()

    context = {"meal_plan": meal_plan, "days": days}
    return render(
        request, "food_application/meal_planning/view_meal_plan.html", context
    )


def delete_meal_plan(request, plan_id):
    """
    Delete a saved meal plan.
    """
    meal_plan = MealPlan.objects.get(id=plan_id)

    if request.method == "POST":
        meal_plan.delete()
        messages.success(request, "Meal plan deleted successfully!")
        return redirect("food_application:saved_meal_plans")

    context = {"meal_plan": meal_plan}
    return render(
        request, "food_application/meal_planning/delete_meal_plan.html", context
    )


def extract_ingredients_from_html(html_content):
    """
    Extract ingredients from HTML recipe content.

    This function parses the HTML from the item_recipe field and attempts to
    extract ingredient lists. It looks for common patterns like:
    - Lists (<ul>, <ol>)
    - Headers with "Ingredients" text
    - Paragraphs that might contain ingredients

    Args:
        html_content: HTML string from the item_recipe field

    Returns:
        A list of ingredient strings
    """
    if not html_content:
        return []

    # Parse HTML
    soup = BeautifulSoup(html_content, "html.parser")
    ingredients = []

    # Method 1: Look for headings containing "ingredient" and get the next list
    ingredient_headers = soup.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "strong"],
        string=re.compile(r"ingredient", re.IGNORECASE),
    )

    for header in ingredient_headers:
        # Find the next <ul> or <ol> after this header
        next_list = header.find_next(["ul", "ol"])
        if next_list:
            for li in next_list.find_all("li"):
                ingredient_text = li.get_text(strip=True)
                if ingredient_text and ingredient_text not in ingredients:
                    ingredients.append(ingredient_text)

    # Method 2: If no ingredients found yet, look for any lists in the content
    if not ingredients:
        all_lists = soup.find_all(["ul", "ol"])
        for list_element in all_lists:
            for li in list_element.find_all("li"):
                ingredient_text = li.get_text(strip=True)
                if ingredient_text and ingredient_text not in ingredients:
                    ingredients.append(ingredient_text)

    return ingredients


def strip_measurements_from_ingredient(ingredient_text):
    """
    Remove measurement amounts from ingredient text, keeping only the ingredient name.

    This function removes:
    - Numbers (whole, fractions, decimals)
    - Common measurement units (cups, tbsp, tsp, oz, lb, etc.)
    - Parenthetical notes

    Args:
        ingredient_text: Full ingredient text with measurements

    Returns:
        Cleaned ingredient name without measurements
    """
    # Pattern to match common measurements at the beginning of the string
    # Matches: numbers, fractions, decimals, and common units
    measurement_pattern = r"^[\d\s/.,½¼¾⅓⅔⅛⅜⅝⅞]*\s*(?:cup|cups|c\.|tablespoon|tablespoons|tbsp|tsp|teaspoon|teaspoons|ounce|ounces|oz|pound|pounds|lb|lbs|gram|grams|g|kilogram|kilograms|kg|milliliter|milliliters|ml|liter|liters|l|pint|pints|pt|quart|quarts|qt|gallon|gallons|gal|piece|pieces|clove|cloves|can|cans|package|packages|pkg|slice|slices|medium|large|small|whole)\s+"

    # Remove measurements from the beginning
    cleaned = re.sub(measurement_pattern, "", ingredient_text, flags=re.IGNORECASE)

    # Remove parenthetical notes like "(optional)" or "(or substitute X)"
    cleaned = re.sub(r"\s*\([^)]*\)", "", cleaned)

    # Remove any leading/trailing whitespace and commas
    cleaned = cleaned.strip().strip(",").strip()

    # Capitalize first letter
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    return cleaned


def shopping_list(request, plan_id):
    """
    Generate and display a shopping list from a meal plan.

    This view:
    1. Gets the meal plan and all its recipes
    2. Extracts ingredients from each recipe's item_recipe field
    3. Compiles them into a unified shopping list with recipe counts
    4. Handles POST requests to remove ingredients user already has at home
    5. Saves or updates the ShoppingList model
    6. Displays the ingredients to the user
    """
    meal_plan = MealPlan.objects.get(id=plan_id)

    # Handle POST request to remove ingredients
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            ingredients_to_remove = data.get("remove_ingredients", [])

            # Get or create the shopping list
            shopping_list_obj, created = ShoppingList.objects.get_or_create(
                meal_plan=meal_plan
            )

            # Get existing excluded ingredients (stored in a new field or use a session)
            # For now, we'll store them in the session
            if "excluded_ingredients" not in request.session:
                request.session["excluded_ingredients"] = {}

            # Add the plan-specific excluded ingredients
            plan_key = f"plan_{plan_id}"
            if plan_key not in request.session["excluded_ingredients"]:
                request.session["excluded_ingredients"][plan_key] = []

            # Add new ingredients to exclude
            for ingredient in ingredients_to_remove:
                if ingredient not in request.session["excluded_ingredients"][plan_key]:
                    request.session["excluded_ingredients"][plan_key].append(ingredient)

            request.session.modified = True

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    # GET request - display the shopping list
    days = meal_plan.days.all()

    # Dictionary to store ingredients by recipe
    recipes_with_ingredients = []
    all_ingredients = []
    ingredient_counter = {}  # Track how many recipes each ingredient appears in

    for day in days:
        if day.recipe:
            # Extract ingredients from the recipe
            ingredients = extract_ingredients_from_html(day.recipe.item_recipe)

            if ingredients:
                recipes_with_ingredients.append(
                    {
                        "recipe_name": day.recipe.item_name,
                        "day": day.day_of_week,
                        "ingredients": ingredients,  # Keep full measurements for "by day" view
                    }
                )
                all_ingredients.extend(ingredients)

                # Strip measurements and count occurrences
                for ingredient in ingredients:
                    cleaned_ingredient = strip_measurements_from_ingredient(ingredient)
                    if cleaned_ingredient:
                        if cleaned_ingredient in ingredient_counter:
                            ingredient_counter[cleaned_ingredient] += 1
                        else:
                            ingredient_counter[cleaned_ingredient] = 1

    # Get excluded ingredients from session
    excluded_ingredients = []
    if "excluded_ingredients" in request.session:
        plan_key = f"plan_{plan_id}"
        excluded_ingredients = request.session["excluded_ingredients"].get(plan_key, [])

    # Filter out excluded ingredients
    ingredient_counter = {
        k: v for k, v in ingredient_counter.items() if k not in excluded_ingredients
    }

    # Convert to list of tuples (ingredient, count) and sort alphabetically
    ingredients_with_counts = sorted(ingredient_counter.items(), key=lambda x: x[0])

    # Get or create the shopping list
    shopping_list_obj, created = ShoppingList.objects.get_or_create(meal_plan=meal_plan)

    # Update the ingredients field (storing as a simple text list without measurements)
    ingredient_list_text = []
    for ingredient, count in ingredients_with_counts:
        if count > 1:
            ingredient_list_text.append(f"{ingredient} (in {count} recipes)")
        else:
            ingredient_list_text.append(ingredient)

    shopping_list_obj.ingredients = "\n".join(ingredient_list_text)
    shopping_list_obj.save()

    context = {
        "meal_plan": meal_plan,
        "recipes_with_ingredients": recipes_with_ingredients,
        "ingredients_with_counts": ingredients_with_counts,  # List of (ingredient, count) tuples
        "shopping_list": shopping_list_obj,
    }

    return render(request, "food_application/meal_planning/shopping_list.html", context)
