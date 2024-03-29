# Django
from django.shortcuts import render, redirect
from django.views.generic import View

# My apps
from movies.models import Movie
from movie_staff.models import MovieStaff

class SearchView(View):
    template_name="search/search.html"
    
    def get(self, request, *args, **kwargs):

        if not request.GET.get("search-bar"):
            return redirect(to="home:home_path")

        search = request.GET.get("search-bar")

        movies = sorted(Movie.objects.filter(name__icontains=search), key=lambda t: t.get_reviews_quantity())[::-1]
        staff = sorted(MovieStaff.objects.filter(name__icontains=search), key=lambda t: t.get_total_review_of_this_staff_movie())[::-1]

        print(staff)
        return render(
            request=request,
            template_name=self.template_name,
            context={
                "search": request.GET.get("search-bar"),
                "movies": movies if request.GET.get("filter") != "1" else None,
                "staff": staff if request.GET.get("filter") != "0" else None,
            }
        )