from django.shortcuts import render
from .forms import GlobalSearchForm
from .services import SearchHandler


def search_view(request):
    """
    Main search view that handles all search types using the SearchHandler service.
    Supports: Research ID, Researcher ID, Keywords, Name prefix, Name contains.
    """
    form = GlobalSearchForm(request.GET or None)

    ctx = {
        "form": form,
        "q": "",
        "researchers": [],
        "research": [],
        "keywords": [],
        "search_type": None,
    }

    if not form.is_valid():
        return render(request, "database/search.html", ctx)

    q = (form.cleaned_data["q"] or "").strip()
    if not q:
        return render(request, "database/search.html", ctx)

    # Use the SearchHandler service to perform the search
    search_result = SearchHandler.search(q)
    ctx.update(search_result)

    return render(request, "database/search.html", ctx)


def home_view(request):
    """Home view that delegates to search view."""
    return search_view(request)
