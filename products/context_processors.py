from .models import Category

def categories(request):
    """
    Context processor to add categories to all templates.
    This makes the categories available in every template.
    """
    return {'categories': Category.objects.all()}
