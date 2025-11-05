from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q  # Import Q for complex queries
from .models import Item
from .forms import ItemForm


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
