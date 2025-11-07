from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q  # Import Q for complex queries
from .models import Item, MealPlan, MealPlanDay
from .forms import ItemForm
from django.contrib import messages


# Create your views here.
def index(request):
    item_list = Item.objects.all()
    context = {"item_list": item_list}
    return render(request, "food_application/index.html", context)


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
    return render(request, "food_application/search_results.html", context)


def detail(request, id):
    item = Item.objects.get(id=id)
    context = {"item": item}
    return render(request, "food_application/detail.html", context)


def create_item(request):
    form = ItemForm(request.POST or None)
    if request.method == "POST":

        if form.is_valid():
            form.save()
            return redirect("food_application:index")

    context = {"form": form}
    return render(request, "food_application/item-form.html", context)


def update_item(request, id):
    item = Item.objects.get(id=id)
    form = ItemForm(request.POST or None, instance=item)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("food_application:index")
    context = {"form": form}
    return render(request, "food_application/recipe_update.html", context)


def delete_item(request, id):
    item = Item.objects.get(id=id)
    if request.method == "POST":
        item.delete()
        return redirect("food_application:index")
    context = {"item": item}
    return render(request, "food_application/delete_recipe.html", context)


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

    return render(request, "food_application/meal_planner.html", context)


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
    return render(request, "food_application/saved_meal_plans.html", context)


def view_meal_plan(request, plan_id):
    """
    View a specific saved meal plan.
    """
    meal_plan = MealPlan.objects.get(id=plan_id)
    # Get all days for this meal plan (automatically ordered by the 'order' field)
    days = meal_plan.days.all()

    context = {"meal_plan": meal_plan, "days": days}
    return render(request, "food_application/view_meal_plan.html", context)


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
    return render(request, "food_application/delete_meal_plan.html", context)
