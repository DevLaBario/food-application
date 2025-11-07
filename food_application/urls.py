from django.urls import path
from . import views


app_name = "food_application"

urlpatterns = [
    path("", views.index, name="index"),
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
    path("<int:id>/", views.detail, name="detail"),
    path("add/", views.create_item, name="create_item"),
    path("update/<int:id>/", views.update_item, name="update_item"),
    path("delete/<int:id>/", views.delete_item, name="delete_item"),
]
