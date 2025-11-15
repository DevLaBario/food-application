from django.urls import path
from . import views


app_name = "food_application"

urlpatterns = [
    path("", views.IndexClassView.as_view(), name="index"),  # Home page URL
    path("search/", views.search, name="search"),  # New search URL
    path(
        "meal-planner/", views.meal_planner, name="meal_planner"
    ),  # Weekly meal planner
    path(
        "meal-planner/save/", views.save_meal_plan, name="save_meal_plan"
    ),  # Save meal plan
    path(
        "meal-planner/saved/", views.saved_meal_plans, name="saved_meal_plans"
    ),  # List saved meal plans
    path(
        "meal-planner/view/<int:plan_id>/", views.view_meal_plan, name="view_meal_plan"
    ),  # View a specific meal plan
    path(
        "meal-planner/delete/<int:plan_id>/",
        views.delete_meal_plan,
        name="delete_meal_plan",
    ),  # Delete meal plan
    path(
        "meal-planner/shopping-list/<int:plan_id>/",
        views.shopping_list,
        name="shopping_list",
    ),  # Shopping list for a meal plan
    path("item/", views.Item, name="item"),
    path(
        "<int:id>/", views.RecipeDetailView.as_view(), name="detail"
    ),  # Detail view for a recipe
    path(
        "add/", views.RecipeCreateView.as_view(), name="create_item"
    ),  # Create new recipe
    path(
        "update/<int:id>/", views.RecipeUpdateView.as_view(), name="update_item"
    ),  # Update existing recipe
    path(
        "delete/<int:id>/", views.RecipeDeleteView.as_view(), name="delete_item"
    ),  # Delete existing recipe
]
