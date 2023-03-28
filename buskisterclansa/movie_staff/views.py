# Django
from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView
from django.http import Http404

# My apps
from extra_logic.functions import object_exist
from movies.models import (
    Director,
    Script,
    Cast,
    Producer,
    CreatedBy,
)

# This app
from .models import MovieStaff

class MovieStaffView(DetailView):
    model = MovieStaff
    context_object_name = "staff"
    template_name = "movie_staff/movie_staff.html"

    def __get_jobs(self, job: str):
        try:
            return {
                "director": self.get_object().movie_director.all().order_by("year"),
                "created_by": self.get_object().movie_created_by.all().order_by("year"),
                "script": self.get_object().movie_script.all().order_by("year"),
                "producer": self.get_object().movie_producer.all().order_by("year"),
                "cast": self.get_object().movie_cast.all().order_by("year"),
            }[job]
        except KeyError:
            raise Http404

    def get_queryset(self):
        return self.model.objects.all()
    
    def get_object(self, *args, **kwargs):
        return get_object_or_404(klass=self.get_queryset(), slug=self.kwargs.get("slug"), pk=self.kwargs.get("pk"))
    
    def get_context_data(self, **kwargs):
        return {
            self.context_object_name: self.get_object(),
            "movies": self.__get_jobs(self.kwargs.get("job")),
            "has_done_job": {
                "director": object_exist(query_str="movie_staff__pk", value_to_query=self.get_object().pk, model=Director),
                "cast": object_exist(query_str="movie_staff__pk", value_to_query=self.get_object().pk, model=Cast),
                "created_by": object_exist(query_str="movie_staff__pk", value_to_query=self.get_object().pk, model=CreatedBy),
                "script": object_exist(query_str="movie_staff__pk", value_to_query=self.get_object().pk, model=Script),
                "producer": object_exist(query_str="movie_staff__pk", value_to_query=self.get_object().pk, model=Producer), 
            },
        }