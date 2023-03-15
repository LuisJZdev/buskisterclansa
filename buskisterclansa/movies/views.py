# Django
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView, View
from django.http import Http404

# This app
from .models import Movie

class MovieView(DetailView):
    model=Movie
    template_name="movies/movie.html"
    context_object_name = "movie"

    def get_queryset(self):
        return self.model.objects.all()

    def get_object(self, *args, **kwargs):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs.get("pk"), slug=self.kwargs.get("slug"))
    
    def get_context_data(self, **kwargs):

        context = {
            self.context_object_name: self.get_object(),
            "directors": self.get_object().directors.all().order_by("director__order"),
            "created_by": self.get_object().created_by.all().order_by("createdby__order"),
            "script": self.get_object().scripts.all().order_by("script__order"),
            "producers": self.get_object().producers.all().order_by("producer__order"),
            "cast": self.get_object().casts.all().order_by("cast__order")[:5],
            "companies": self.get_object().producer_companies.all(),
            "cast_len": len(self.get_object().casts.all().order_by("cast__order")),
        }

        return context
    
class DragMovieStaffView(View):

    def dispatch(self, request, *args, **kwargs):
        self.movie = get_object_or_404(klass=Movie, pk=kwargs.get("pk"), slug=kwargs.get("slug"))
        if request.user.is_authenticated:
            if request.user.is_admin:
                return super().dispatch(request, *args, **kwargs)

        raise Http404

    def __get_relation_staff(self):
        return {
                "created_by": self.movie.createdby_set.all().order_by("order"),
                "cast": self.movie.cast_set.all().order_by("order"),
                "director": self.movie.director_set.all().order_by("order"),
                "producer": self.movie.producer_set.all().order_by("order"),
                "script": self.movie.script_set.all().order_by("order"),
            }

    def get(self, request, *args, **kwargs):
        
        if not self.__get_relation_staff().get(self.kwargs.get("job")):
            raise Http404

        return render(
            request=request,
            template_name="movies/drag_movie_staff.html",
            context={
                "objects": self.__get_relation_staff()[self.kwargs.get("job")], 
                "job": self.kwargs.get("job"),
                "pk": self.kwargs.get("pk"),
                "slug": self.kwargs.get("slug"),
            }
        )
    
    def post(self, request, *args, **kwargs):
        staff = self.__get_relation_staff().get(self.kwargs.get("job"))
        if not staff:
            raise Http404
        request_post = dict(request.POST)
        request_post.pop("csrfmiddlewaretoken")

        iterator = 0
        for person_id in request_post.values():
            person = staff.get(id=person_id[0])
            person.order = iterator
            person.save()
            iterator += 1

        return redirect(to="movies:drag_movie_staff_path", slug=self.kwargs.get("slug"), pk=self.kwargs.get("pk"), job=self.kwargs.get("job") )
