# 🗄️ Database Architecture & Function Breakdown

## Table of Contents
1. [Database Structure Overview](#database-structure-overview)
2. [Model Relationships Explained](#model-relationships-explained)
3. [How Data Flows Through the System](#how-data-flows-through-the-system)
4. [Function-by-Function Breakdown](#function-by-function-breakdown)
5. [Real-World Example](#real-world-example)

---

## Database Structure Overview

Your food application has **4 main database tables** (models):

```
┌─────────────────┐
│      Item       │  ← Recipes/Food Items (independent)
│  (Recipes)      │
└─────────────────┘
         ↑
         │ ForeignKey (recipe)
         │ SET_NULL
         │
┌─────────────────┐     ┌──────────────────┐
│   MealPlan      │────→│  MealPlanDay     │
│  (Weekly Plan)  │  1  │  (Days of Week)  │  many
└─────────────────┘     └──────────────────┘
         │
         │ OneToOneField
         │ CASCADE
         ↓
┌─────────────────┐
│  ShoppingList   │
│  (Ingredients)  │
└─────────────────┘
```

### The 4 Models:

1. **Item** - Individual recipes/food items
2. **MealPlan** - A saved weekly plan (container)
3. **MealPlanDay** - Links recipes to specific days in a plan
4. **ShoppingList** - Compiled ingredients from a meal plan

---

## Model Relationships Explained

### 1. Item Model (The Foundation)
```python
class Item(models.Model):
    item_name = models.CharField(max_length=100)
    item_description = models.CharField(max_length=200)
    item_recipe = HTMLField()  # Contains ingredients!
    item_price = models.IntegerField()
    item_image = models.CharField(max_length=500)
```

**Purpose**: Stores individual recipes/food items  
**Relationship**: None - It's independent! Other models reference it.  
**Real-world example**: "Spaghetti Carbonara" recipe with ingredients list

---

### 2. MealPlan Model (The Container)
```python
class MealPlan(models.Model):
    name = models.CharField(max_length=200, default="My Meal Plan")
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
```

**Purpose**: Represents a saved weekly meal plan  
**Relationship**: Has many `MealPlanDay` entries (one-to-many)  
**Real-world example**: "Holiday Week Menu" created on Nov 7, 2025

**Key Features**:
- `related_name="days"` in MealPlanDay allows: `meal_plan.days.all()`
- `ordering = ["-created_at"]` - Shows newest plans first

---

### 3. MealPlanDay Model (The Junction/Bridge)
```python
class MealPlanDay(models.Model):
    meal_plan = models.ForeignKey(
        MealPlan,
        on_delete=models.CASCADE,  # Delete days if plan deleted
        related_name="days"
    )
    day_of_week = models.CharField(max_length=20)
    recipe = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,  # Keep day if recipe deleted
        null=True
    )
    order = models.IntegerField(default=0)
```

**Purpose**: Links recipes to specific days in a meal plan  
**Relationship**: 
- Belongs to ONE MealPlan (many-to-one)
- References ONE Item/recipe (many-to-one)

**Why This Exists**: 
You can't directly connect MealPlan to Item because you need to know:
- Which day of the week?
- What order?
- Which specific plan?

**Real-world example**: "Monday: Spaghetti, Tuesday: Tacos, Wednesday: Salad"

**Key Deletion Behaviors**:
- `CASCADE` on meal_plan: If you delete a MealPlan, all its days are deleted too
- `SET_NULL` on recipe: If you delete a recipe, the day stays but shows "No recipe"

---

### 4. ShoppingList Model (The Aggregator)
```python
class ShoppingList(models.Model):
    meal_plan = models.OneToOneField(
        MealPlan,
        on_delete=models.CASCADE,
        related_name="shopping_list"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    ingredients = models.TextField(blank=True)
```

**Purpose**: Stores compiled ingredients from all recipes in a meal plan  
**Relationship**: Belongs to ONE MealPlan (one-to-one)  
**Real-world example**: "Shopping list for Holiday Week Menu: eggs, pasta, tomatoes..."

**Key Feature**:
- `OneToOneField`: Each MealPlan can have only ONE ShoppingList
- `related_name="shopping_list"` allows: `meal_plan.shopping_list`
- Ingredients compiled from all recipes in the plan

---

## How Data Flows Through the System

### Flow 1: Creating a Meal Plan
```
User creates meal plan
        ↓
save_meal_plan() function called
        ↓
1. MealPlan.objects.create(name="My Plan")
   Creates new MealPlan record
        ↓
2. For each day (Monday-Sunday):
   MealPlanDay.objects.create(
       meal_plan=meal_plan,    ← Links to MealPlan
       recipe=selected_recipe,  ← Links to Item
       day_of_week="Monday",
       order=0
   )
        ↓
Database now has:
- 1 MealPlan record
- 7 MealPlanDay records (all linked to that plan)
```

### Flow 2: Generating a Shopping List
```
User clicks "Generate Shopping List"
        ↓
shopping_list() function called
        ↓
1. Get MealPlan by ID
   meal_plan = MealPlan.objects.get(id=plan_id)
        ↓
2. Get all days in that plan
   days = meal_plan.days.all()  ← Uses related_name!
        ↓
3. For each day:
   - Get the recipe: day.recipe
   - Extract ingredients from: day.recipe.item_recipe
        ↓
4. Create/update ShoppingList
   shopping_list_obj, created = ShoppingList.objects.get_or_create(
       meal_plan=meal_plan
   )
        ↓
5. Save all ingredients
   shopping_list_obj.ingredients = "\n".join(all_ingredients)
   shopping_list_obj.save()
        ↓
Display to user!
```

---

## Function-by-Function Breakdown

### 🔍 Database Query Functions

#### 1. `Item.objects.all()`
```python
# views.py - index function
item_list = Item.objects.all()
```
**What it does**: Retrieves ALL recipes from the Item table  
**SQL equivalent**: `SELECT * FROM item;`  
**Returns**: QuerySet of all Item objects  
**Used in**: Homepage to display all recipes

---

#### 2. `Item.objects.get(id=id)`
```python
# views.py - detail function
item = Item.objects.get(id=id)
```
**What it does**: Retrieves ONE specific recipe by its ID  
**SQL equivalent**: `SELECT * FROM item WHERE id = 5;`  
**Returns**: Single Item object  
**Raises**: DoesNotExist error if not found  
**Used in**: Viewing recipe details, updating, deleting

---

#### 3. `Item.objects.filter(Q(...))`
```python
# views.py - search function
results = Item.objects.filter(
    Q(item_name__icontains=query) | 
    Q(item_description__icontains=query)
).distinct()
```
**What it does**: Searches recipes matching criteria  
**SQL equivalent**: 
```sql
SELECT DISTINCT * FROM item 
WHERE item_name LIKE '%pizza%' 
   OR item_description LIKE '%pizza%';
```
**Returns**: QuerySet of matching items  
**Key features**:
- `Q()` allows OR conditions
- `__icontains` = case-insensitive partial match
- `.distinct()` removes duplicates

---

#### 4. `MealPlan.objects.create(name=plan_name)`
```python
# views.py - save_meal_plan function
meal_plan = MealPlan.objects.create(name=plan_name)
```
**What it does**: Creates a new MealPlan record in the database  
**SQL equivalent**: 
```sql
INSERT INTO mealplan (name, created_at, notes) 
VALUES ('My Plan', NOW(), NULL);
```
**Returns**: The newly created MealPlan object  
**Auto-sets**: created_at field (because of auto_now_add=True)

---

#### 5. `MealPlanDay.objects.create(...)`
```python
# views.py - save_meal_plan function
MealPlanDay.objects.create(
    meal_plan=meal_plan,      # ForeignKey to MealPlan
    day_of_week=day,          # "Monday"
    recipe=recipe,            # ForeignKey to Item
    order=index               # 0-6
)
```
**What it does**: Creates a link between a meal plan, day, and recipe  
**SQL equivalent**:
```sql
INSERT INTO mealplanday (meal_plan_id, day_of_week, recipe_id, order) 
VALUES (1, 'Monday', 5, 0);
```
**Returns**: The newly created MealPlanDay object  
**Creates relationships**: Links to both MealPlan and Item tables

---

#### 6. `meal_plan.days.all()`
```python
# views.py - view_meal_plan function
days = meal_plan.days.all()
```
**What it does**: Gets all MealPlanDay records for a specific meal plan  
**SQL equivalent**:
```sql
SELECT * FROM mealplanday 
WHERE meal_plan_id = 1 
ORDER BY order;
```
**Returns**: QuerySet of MealPlanDay objects  
**Why it works**: `related_name="days"` in the MealPlanDay model  
**Auto-ordered**: By the `order` field (0-6 for Mon-Sun)

---

#### 7. `ShoppingList.objects.get_or_create(meal_plan=meal_plan)`
```python
# views.py - shopping_list function
shopping_list_obj, created = ShoppingList.objects.get_or_create(
    meal_plan=meal_plan
)
```
**What it does**: 
- First tries to GET an existing ShoppingList for this meal plan
- If not found, CREATES a new one

**SQL equivalent**:
```sql
-- First tries:
SELECT * FROM shoppinglist WHERE meal_plan_id = 1;
-- If not found, runs:
INSERT INTO shoppinglist (meal_plan_id, created_at, ingredients) 
VALUES (1, NOW(), '');
```

**Returns**: Tuple of (object, created_boolean)
- `shopping_list_obj` = the ShoppingList object
- `created` = True if newly created, False if already existed

**Why this is useful**: Prevents duplicate shopping lists for the same plan

---

### 🔧 Helper Functions

#### 8. `extract_ingredients_from_html(html_content)`
```python
def extract_ingredients_from_html(html_content):
    if not html_content:
        return []
    
    soup = BeautifulSoup(html_content, "html.parser")
    ingredients = []
    
    # Method 1: Find "Ingredients" header + next list
    ingredient_headers = soup.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "strong"],
        string=re.compile(r"ingredient", re.IGNORECASE)
    )
    
    for header in ingredient_headers:
        next_list = header.find_next(["ul", "ol"])
        if next_list:
            for li in next_list.find_all("li"):
                ingredient_text = li.get_text(strip=True)
                if ingredient_text and ingredient_text not in ingredients:
                    ingredients.append(ingredient_text)
    
    # Method 2: If nothing found, get any lists
    if not ingredients:
        all_lists = soup.find_all(["ul", "ol"])
        for list_element in all_lists:
            for li in list_element.find_all("li"):
                ingredient_text = li.get_text(strip=True)
                if ingredient_text and ingredient_text not in ingredients:
                    ingredients.append(ingredient_text)
    
    return ingredients
```

**What it does**: Parses HTML from `item_recipe` field to extract ingredient lists  
**Input**: HTML string like:
```html
<h3>Ingredients</h3>
<ul>
    <li>2 eggs</li>
    <li>1 cup flour</li>
</ul>
```
**Output**: Python list: `["2 eggs", "1 cup flour"]`

**How it works**:
1. **Parse HTML**: Uses BeautifulSoup to convert HTML string into searchable structure
2. **Find Headers**: Looks for any heading containing "ingredient" (case-insensitive)
3. **Get Next List**: Finds the `<ul>` or `<ol>` after that heading
4. **Extract Items**: Gets text from each `<li>` tag
5. **Fallback**: If no header found, searches for ANY lists in the HTML
6. **Deduplicate**: Checks `ingredient_text not in ingredients` to avoid duplicates

**Key Tools Used**:
- `BeautifulSoup(html_content, "html.parser")` - Parses HTML
- `soup.find_all([tags], string=pattern)` - Finds matching elements
- `header.find_next([tags])` - Gets next element of specific type
- `li.get_text(strip=True)` - Extracts clean text without HTML tags
- `re.compile(r"ingredient", re.IGNORECASE)` - Case-insensitive regex match

---

### 🎯 View Functions (Request → Database → Response)

#### 9. `save_meal_plan(request)`
```python
def save_meal_plan(request):
    if request.method == "POST":
        plan_name = request.POST.get("plan_name", "My Meal Plan")
        
        # CREATE: New MealPlan
        meal_plan = MealPlan.objects.create(name=plan_name)
        
        days = ["Monday", "Tuesday", ..., "Sunday"]
        
        for index, day in enumerate(days):
            recipe_id = request.POST.get(f"recipe_{day}")
            
            if recipe_id and recipe_id != "None":
                try:
                    # GET: Recipe by ID
                    recipe = Item.objects.get(id=recipe_id)
                    
                    # CREATE: Link day to plan and recipe
                    MealPlanDay.objects.create(
                        meal_plan=meal_plan,
                        day_of_week=day,
                        recipe=recipe,
                        order=index
                    )
                except Item.DoesNotExist:
                    pass
        
        messages.success(request, f"Meal plan '{plan_name}' saved!")
        return redirect("food_application:saved_meal_plans")
```

**Flow**:
1. **Receives POST data** from form submission
2. **Gets plan name** from `request.POST.get("plan_name")`
3. **Creates MealPlan** → 1 database INSERT
4. **Loops through 7 days**:
   - Gets recipe ID from form: `recipe_Monday`, `recipe_Tuesday`, etc.
   - Retrieves recipe: `Item.objects.get(id=recipe_id)` → SELECT query
   - Creates MealPlanDay: → INSERT query
5. **Total DB operations**: 1 INSERT (MealPlan) + up to 7 SELECTs + up to 7 INSERTs (days)

**Form data received**:
```
plan_name: "Holiday Menu"
recipe_Monday: "5"
recipe_Tuesday: "12"
recipe_Wednesday: "3"
...
```

---

#### 10. `shopping_list(request, plan_id)`
```python
def shopping_list(request, plan_id):
    # GET: Meal plan by ID
    meal_plan = MealPlan.objects.get(id=plan_id)
    
    # GET: All days for this plan (uses ForeignKey relationship)
    days = meal_plan.days.all()
    
    recipes_with_ingredients = []
    all_ingredients = []
    
    # Loop through each day
    for day in days:
        if day.recipe:  # If there's a recipe for this day
            # Extract ingredients from HTML
            ingredients = extract_ingredients_from_html(day.recipe.item_recipe)
            
            if ingredients:
                recipes_with_ingredients.append({
                    "recipe_name": day.recipe.item_name,
                    "day": day.day_of_week,
                    "ingredients": ingredients
                })
                all_ingredients.extend(ingredients)
    
    # GET or CREATE: Shopping list for this plan
    shopping_list_obj, created = ShoppingList.objects.get_or_create(
        meal_plan=meal_plan
    )
    
    # UPDATE: Save ingredients
    shopping_list_obj.ingredients = "\n".join(all_ingredients)
    shopping_list_obj.save()
    
    context = {
        "meal_plan": meal_plan,
        "recipes_with_ingredients": recipes_with_ingredients,
        "all_ingredients": all_ingredients,
        "shopping_list": shopping_list_obj,
    }
    
    return render(request, "food_application/meal_planning/shopping_list.html", context)
```

**Database Operations**:
1. `MealPlan.objects.get(id=plan_id)` → 1 SELECT from mealplan table
2. `meal_plan.days.all()` → 1 SELECT from mealplanday table (gets all days for this plan)
3. `day.recipe` → Uses JOIN to get Item data (already loaded with days)
4. `ShoppingList.objects.get_or_create()` → 1 SELECT, maybe 1 INSERT
5. `shopping_list_obj.save()` → 1 UPDATE

**Total**: ~4-5 database queries

**Data Flow**:
```
Plan ID: 5
    ↓
Get MealPlan (id=5) → "Holiday Menu"
    ↓
Get all MealPlanDays where meal_plan_id=5
    ↓
[
  {day: "Monday", recipe_id: 3},
  {day: "Tuesday", recipe_id: 7},
  ...
]
    ↓
For each day, get recipe.item_recipe (HTML)
    ↓
Extract ingredients from HTML using BeautifulSoup
    ↓
Compile all ingredients into list
    ↓
Save to ShoppingList.ingredients field
    ↓
Display to user
```

---

## Real-World Example

Let's trace a complete user journey through the database:

### Step 1: User Creates Recipes
```python
# User creates 3 recipes via admin or create_item()
Item.objects.create(
    item_name="Spaghetti Carbonara",
    item_recipe="<h3>Ingredients</h3><ul><li>400g spaghetti</li><li>4 eggs</li></ul>",
    item_price=12
)
Item.objects.create(
    item_name="Caesar Salad",
    item_recipe="<h3>Ingredients</h3><ul><li>Romaine lettuce</li><li>Croutons</li></ul>",
    item_price=8
)
```

**Database State**:
```
Item Table:
+----+---------------------+------------------+-------+
| id | item_name           | item_recipe      | price |
+----+---------------------+------------------+-------+
| 1  | Spaghetti Carbonara | <html>...</html> | 12    |
| 2  | Caesar Salad        | <html>...</html> | 8     |
+----+---------------------+------------------+-------+
```

---

### Step 2: User Creates a Meal Plan
```python
# User visits /meal-planner/ and saves a plan
save_meal_plan(request) called with:
    plan_name = "Work Week Meals"
    recipe_Monday = "1"    # Spaghetti
    recipe_Tuesday = "2"   # Salad
    recipe_Wednesday = "1" # Spaghetti again
```

**Code Execution**:
```python
# Creates MealPlan
meal_plan = MealPlan.objects.create(name="Work Week Meals")
# → INSERT INTO mealplan (id=1, name="Work Week Meals", created_at=NOW())

# Creates MealPlanDay for Monday
recipe = Item.objects.get(id=1)  # Gets Spaghetti
# → SELECT * FROM item WHERE id=1
MealPlanDay.objects.create(meal_plan=meal_plan, day_of_week="Monday", recipe=recipe, order=0)
# → INSERT INTO mealplanday (meal_plan_id=1, day_of_week="Monday", recipe_id=1, order=0)

# Creates MealPlanDay for Tuesday
recipe = Item.objects.get(id=2)  # Gets Salad
# → SELECT * FROM item WHERE id=2
MealPlanDay.objects.create(meal_plan=meal_plan, day_of_week="Tuesday", recipe=recipe, order=1)
# → INSERT INTO mealplanday (meal_plan_id=1, day_of_week="Tuesday", recipe_id=2, order=1)
```

**Database State**:
```
MealPlan Table:
+----+------------------+---------------------+
| id | name             | created_at          |
+----+------------------+---------------------+
| 1  | Work Week Meals  | 2025-11-07 10:30:00 |
+----+------------------+---------------------+

MealPlanDay Table:
+----+--------------+-------------+-----------+-------+
| id | meal_plan_id | day_of_week | recipe_id | order |
+----+--------------+-------------+-----------+-------+
| 1  | 1            | Monday      | 1         | 0     |
| 2  | 1            | Tuesday     | 2         | 1     |
| 3  | 1            | Wednesday   | 1         | 2     |
+----+--------------+-------------+-----------+-------+
```

---

### Step 3: User Views the Meal Plan
```python
# User visits /meal-planner/view/1/
view_meal_plan(request, plan_id=1)

# Gets the meal plan
meal_plan = MealPlan.objects.get(id=1)
# → SELECT * FROM mealplan WHERE id=1
# Returns: MealPlan(id=1, name="Work Week Meals")

# Gets all days for this plan
days = meal_plan.days.all()
# → SELECT * FROM mealplanday WHERE meal_plan_id=1 ORDER BY order
# Returns: [MealPlanDay(...), MealPlanDay(...), MealPlanDay(...)]
```

**SQL Behind the Scenes**:
```sql
-- Get meal plan
SELECT * FROM mealplan WHERE id = 1;

-- Get all days (with JOINs to get recipe data)
SELECT 
    mealplanday.id,
    mealplanday.day_of_week,
    mealplanday.order,
    item.item_name,
    item.item_description,
    item.item_image,
    item.item_price
FROM mealplanday
LEFT JOIN item ON mealplanday.recipe_id = item.id
WHERE mealplanday.meal_plan_id = 1
ORDER BY mealplanday.order;
```

**Template Receives**:
```python
context = {
    "meal_plan": <MealPlan: Work Week Meals>,
    "days": [
        <MealPlanDay: Monday - Spaghetti Carbonara>,
        <MealPlanDay: Tuesday - Caesar Salad>,
        <MealPlanDay: Wednesday - Spaghetti Carbonara>
    ]
}
```

---

### Step 4: User Generates Shopping List
```python
# User clicks "Generate Shopping List" → visits /meal-planner/shopping-list/1/
shopping_list(request, plan_id=1)

# Get the meal plan
meal_plan = MealPlan.objects.get(id=1)
# → SELECT * FROM mealplan WHERE id=1

# Get all days
days = meal_plan.days.all()
# → SELECT * FROM mealplanday WHERE meal_plan_id=1

# Loop through days
for day in days:  # Monday, Tuesday, Wednesday
    if day.recipe:
        # Extract ingredients
        ingredients = extract_ingredients_from_html(day.recipe.item_recipe)
        # Monday: ["400g spaghetti", "4 eggs"]
        # Tuesday: ["Romaine lettuce", "Croutons"]
        # Wednesday: ["400g spaghetti", "4 eggs"] (duplicate!)
```

**Ingredient Extraction Process**:
```python
# For Monday's Spaghetti:
html = "<h3>Ingredients</h3><ul><li>400g spaghetti</li><li>4 eggs</li></ul>"
soup = BeautifulSoup(html, "html.parser")

# Finds <h3>Ingredients</h3>
header = soup.find_all(string=re.compile(r"ingredient", re.IGNORECASE))
# Returns: ["Ingredients"]

# Gets next <ul> after the header
next_list = header.find_next(["ul", "ol"])
# Returns: <ul><li>400g spaghetti</li><li>4 eggs</li></ul>

# Extracts <li> items
for li in next_list.find_all("li"):
    ingredient = li.get_text(strip=True)
    # First iteration: "400g spaghetti"
    # Second iteration: "4 eggs"
    ingredients.append(ingredient)

# Final result: ["400g spaghetti", "4 eggs"]
```

**Creates Shopping List**:
```python
# Get or create shopping list
shopping_list_obj, created = ShoppingList.objects.get_or_create(meal_plan=meal_plan)
# → SELECT * FROM shoppinglist WHERE meal_plan_id=1
# If not found: INSERT INTO shoppinglist (meal_plan_id=1, created_at=NOW())

# All ingredients (with duplicates)
all_ingredients = [
    "400g spaghetti", "4 eggs",           # Monday
    "Romaine lettuce", "Croutons",        # Tuesday
    "400g spaghetti", "4 eggs"            # Wednesday (duplicates)
]

# Save to database
shopping_list_obj.ingredients = "\n".join(all_ingredients)
# → "400g spaghetti\n4 eggs\nRomaine lettuce\nCroutons\n400g spaghetti\n4 eggs"
shopping_list_obj.save()
# → UPDATE shoppinglist SET ingredients='...' WHERE id=1
```

**Final Database State**:
```
ShoppingList Table:
+----+--------------+---------------------+------------------------------------+
| id | meal_plan_id | created_at          | ingredients                        |
+----+--------------+---------------------+------------------------------------+
| 1  | 1            | 2025-11-07 11:00:00 | 400g spaghetti                     |
|    |              |                     | 4 eggs                             |
|    |              |                     | Romaine lettuce                    |
|    |              |                     | Croutons                           |
|    |              |                     | 400g spaghetti                     |
|    |              |                     | 4 eggs                             |
+----+--------------+---------------------+------------------------------------+
```

---

## Key Concepts Explained

### ForeignKey vs OneToOneField

**ForeignKey** (Many-to-One):
- Many MealPlanDays can reference ONE MealPlan
- Many MealPlanDays can reference ONE recipe
- Example: Multiple days can have the same recipe

**OneToOneField** (One-to-One):
- ONE ShoppingList per MealPlan
- Each MealPlan can have only ONE ShoppingList
- Example: You don't want duplicate shopping lists

### on_delete Behaviors

**CASCADE**: "If parent is deleted, delete me too"
- Delete MealPlan → Deletes all MealPlanDays
- Delete MealPlan → Deletes ShoppingList

**SET_NULL**: "If parent is deleted, set my reference to NULL"
- Delete Item/recipe → MealPlanDay keeps existing but recipe becomes None
- Useful when you want to preserve the meal plan structure

### related_name Magic

```python
# In MealPlanDay model:
meal_plan = models.ForeignKey(MealPlan, related_name="days")

# Allows reverse lookup:
meal_plan = MealPlan.objects.get(id=1)
days = meal_plan.days.all()  # ← This works because of related_name!

# In ShoppingList model:
meal_plan = models.OneToOneField(MealPlan, related_name="shopping_list")

# Allows:
meal_plan = MealPlan.objects.get(id=1)
shopping = meal_plan.shopping_list  # ← Direct access!
```

---

## Summary of Database Interactions

| Function | Database Tables Used | Type of Query | Purpose |
|----------|---------------------|---------------|---------|
| `index()` | Item | SELECT all | Display all recipes |
| `detail()` | Item | SELECT one | Show recipe details |
| `search()` | Item | SELECT filtered | Find recipes |
| `save_meal_plan()` | MealPlan, MealPlanDay, Item | INSERT, SELECT | Save weekly plan |
| `view_meal_plan()` | MealPlan, MealPlanDay, Item | SELECT with JOIN | Display saved plan |
| `delete_meal_plan()` | MealPlan (CASCADE to others) | DELETE | Remove plan |
| `shopping_list()` | All 4 tables | SELECT, INSERT/UPDATE | Generate ingredient list |

### Total Tables in Database: **4**
1. Item (recipes)
2. MealPlan (weekly plans)
3. MealPlanDay (junction table)
4. ShoppingList (compiled ingredients)

### Relationship Summary:
```
Item ←──── MealPlanDay ────→ MealPlan ──→ ShoppingList
 ^                                ^
 └────────────────────────────────┘
         (many items can be      (one shopping list
          in many plans)          per meal plan)
```

---

## Practice Questions to Test Your Understanding

1. What happens to MealPlanDays if you delete a MealPlan?
2. What happens to MealPlanDays if you delete an Item/recipe?
3. How does `meal_plan.days.all()` work? What SQL does it generate?
4. Why do we use `get_or_create()` for ShoppingList instead of just `create()`?
5. What does BeautifulSoup do in the ingredient extraction?
6. How many database queries run when viewing a meal plan?

**Answers**:
1. CASCADE - They get deleted too
2. SET_NULL - They stay but recipe becomes None
3. Uses related_name to do reverse lookup; SQL: `SELECT * FROM mealplanday WHERE meal_plan_id = X`
4. Prevents creating duplicate shopping lists for the same plan
5. Parses HTML to extract text from `<li>` tags containing ingredients
6. Minimum 2: one for MealPlan, one for all MealPlanDays (may JOIN with Items)
