from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.urls import reverse_lazy


# Create your views here.
# def register(request):
#     if request.method == "POST":
#         form = UserRegisterForm(request.POST)
#         if form.is_valid():
#             form.save()
#             username = form.cleaned_data.get("username")
#             messages.success(
#                 request, f"Account created for {username} and login successful"
#             )
#             return redirect("users:login")
#     else:
#         form = UserRegisterForm()
#     return render(request, "users/register.html", {"form": form})


class RegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")


def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return render(request, "users/logout.html")


@login_required
def profile(request):
    from food_application.models import Item, MealPlan

    # Get counts - universal for all users
    total_recipes = Item.objects.count()
    total_meal_plans = MealPlan.objects.count()

    # Get member since year
    member_since = request.user.date_joined.year

    context = {
        "total_recipes": total_recipes,
        "total_meal_plans": total_meal_plans,
        "member_since": member_since,
    }

    return render(request, "users/profile.html", context)
