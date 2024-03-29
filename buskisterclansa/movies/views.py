# Django
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView, ListView, View
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist

# My apps
from movie_staff.models import MovieStaff
from extra_logic.movies.functions import get_dependant_object_if_it_exist, like_dislike
from extra_logic.functions import make_pagination, get_pagination_numbers, int_or_404

# This app
from .models import Movie, Review, ReviewComment
from .forms import ReviewForm, ReviewCommentForm

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
            "directors": self.get_object().directors.all().order_by("director__order")[:3],
            "script": self.get_object().scripts.all().order_by("script__order")[:3],
            "producers": self.get_object().producers.all().order_by("producer__order")[:3],
            "cast": self.get_object().casts.all().order_by("cast__order")[:3],
            "companies": self.get_object().producer_companies.all(),
            "cast_len": len(self.get_object().casts.all().order_by("cast__order")),
            "movie_pk": self.kwargs.get("pk"),
            "movie_slug": self.kwargs.get("slug"),

            "reviews": self.get_object().review_set.all().order_by("-pk")[:5],
            "stars_rating": (
                "",
                len(self.get_object().review_set.filter(rate_by_stars=1)),
                len(self.get_object().review_set.filter(rate_by_stars=2)),
                len(self.get_object().review_set.filter(rate_by_stars=3)),
                len(self.get_object().review_set.filter(rate_by_stars=4)),
                len(self.get_object().review_set.filter(rate_by_stars=5)),
            )
        }
        
        return context
    
class DragMovieStaffView(View):
    """
    This view is to change the order in which the staff of a movie is showed. In a movie 
    there are more important characters than others, you won't show an extra before the main characters,
    they must have an order of appearance, and, changeable, this is achieved with a draggable list with JS
    """
    def dispatch(self, request, *args, **kwargs):
        self.movie = get_object_or_404(klass=Movie, pk=kwargs.get("pk"), slug=kwargs.get("slug"))
        if request.user.is_authenticated:
            if request.user.is_admin:
                return super().dispatch(request, *args, **kwargs)

        raise Http404

    def __get_relation_staff(self):
        return {
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
    
class MovieReviewsListView(ListView):
    template_name = "movies/reviews.html"
    context_object_name = "reviews"

    # The goal of this methods and this way I'm sending and receiving the filters is to not 
    # put query names (like "person__pk" for example) in the endpoints, making it more secure of injections
    def __get_orders_indexes(self):
        return {
            "stars (higher to lower)": "0",
            "stars (lower to higher)": "1",
        }
    def __get_orders_queries(self, ):
        return (
            "-rate_by_stars",
            "rate_by_stars",
        )
    def __get_index_order_or_404(self):
        return self.__get_orders_queries()[int_or_404(self.request.GET.get("order"))]

        
    def __get_filters(self):
        return {
            "5 stars": "5",
            "4 stars": "4",
            "3 stars": "3",
            "2 stars": "2",
            "1 stars": "1",
        }

    def dispatch(self, request, *args, **kwargs):
        self.movie = get_object_or_404(klass=Movie, slug=self.kwargs.get("slug"), pk=self.kwargs.get("pk"))
        
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.movie.review_set.all()

    def get_context_data(self, **kwargs):

        reviews = self.get_queryset()
        page = None
        if self.request.GET.get("page"):
            page = int_or_404(self.request.GET.get("page"))
        else:
            page = 1

        if not self.request.GET.get("filter") and not self.request.GET.get("order"):
            reviews = reviews.order_by("-pk")

        if self.request.GET.get("filter"):
            reviews = reviews.filter(rate_by_stars=int_or_404(self.request.GET.get("filter")))
        if self.request.GET.get("order"):
            reviews = reviews.order_by(self.__get_index_order_or_404())

        number_of_pages = get_pagination_numbers(reviews, 5)

        if page and page != 0:
            aux = reviews
            reviews = make_pagination(reviews, page, 5)
            if not reviews:
                reviews = make_pagination(aux, 1, 5)
                page = 1
        else:
            reviews = make_pagination(reviews, 1, 5)

        return {
            self.context_object_name: reviews,
            "movie": self.movie,
            "stars_rating": (
                "",
                len(self.movie.review_set.filter(rate_by_stars=1)),
                len(self.movie.review_set.filter(rate_by_stars=2)),
                len(self.movie.review_set.filter(rate_by_stars=3)),
                len(self.movie.review_set.filter(rate_by_stars=4)),
                len(self.movie.review_set.filter(rate_by_stars=5)),
            ),
            "orders": self.__get_orders_indexes(),
            "filters": self.__get_filters(),
            "number_of_pages": number_of_pages,

            "selected_order": self.request.GET.get("order"),
            "selected_filter": self.request.GET.get("filter"),
            "selected_page": page,

            "previous_page": page - 1 if page > 1 and number_of_pages > 1 else None,
            "next_page": page + 1 if page != number_of_pages and number_of_pages > 1 else None,
        }
    
class AddReviewView(View):

    def dispatch(self, request, *args, **kwargs):
        self.movie = get_object_or_404(klass=Movie, slug=self.kwargs.get("slug"), pk=self.kwargs.get("pk"))
        self.comment = get_dependant_object_if_it_exist(self.movie.review_set, request.user.pk, "user__pk")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        return render(
            request=request,
            template_name="movies/add_review.html",
            context= {
                "movie_name": self.movie.name,
                "movie_slug": self.kwargs.get("slug"),
                "movie_pk": self.kwargs.get("pk"),
                "comment": self.comment,
            }
        )
    
    def post(self, request, *args, **kwargs):
        form = ReviewForm(request.POST)

        if form.is_valid():
            if self.comment:
                self.comment.name=request.POST["name"]
                self.comment.content=request.POST["content"]
                self.comment.rate_by_stars=request.POST["rate_by_stars"]
                self.comment.save()
            else:
                self.movie.review_set.create(
                    user=request.user,
                    name=request.POST["name"],
                    content=request.POST["content"],
                    rate_by_stars=request.POST["rate_by_stars"],
                )
            return redirect(to="movies:movie_path", slug=self.kwargs.get("slug"), pk=self.kwargs.get("pk"))
        else:
            return render(
                request=request,
                template_name="movies/add_review.html",
                context= {
                    "movie_name": self.movie.name,
                    "movie_slug": self.kwargs.get("slug"),
                    "movie_pk": self.kwargs.get("pk"),
                    "comment": self.comment,
                    "errors": dict(form.errors),
                }
            )
        
class DeleteReviewView(View):
    def post(self, request, *args, **kwargs):
        self.movie = get_object_or_404(klass=Movie, slug=self.kwargs.get("slug"), pk=self.kwargs.get("pk"))
        self.comment = get_dependant_object_if_it_exist(self.movie.review_set, request.user.pk, "user__pk")

        if self.comment: 
            self.comment.delete()
        
        return redirect(to="movies:movie_path", slug=self.kwargs.get("slug"), pk=self.kwargs.get("pk"))

class ReviewDetailView(DetailView):
    template_name="movies/show_review.html"
    context_object_name="review"

    def dispatch(self, request, *args, **kwargs):
        self.movie = get_object_or_404(klass=Movie, slug=self.kwargs.get("slug"), pk=self.kwargs.get("pk"))
        
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.movie.review_set.all()
    
    def get_object(self, *args, **kwargs):
        return get_object_or_404(klass=self.get_queryset(), pk=self.kwargs.get("review_pk"))
    
    def get_context_data(self, **kwargs):
        return {
            self.context_object_name: self.get_object(),
            "movie": self.movie,
            "has_like": self.get_object().has_like_or_dislike(option=1, user_pk=self.request.user.pk) if self.request.user.is_authenticated else None,
            "has_dislike": self.get_object().has_like_or_dislike(option=2, user_pk=self.request.user.pk) if self.request.user.is_authenticated else None,
            "like_counter": len(self.get_object().reviewlike_set.all()),
            "dislike_counter": len(self.get_object().reviewdislike_set.all()),

            "comments": self.get_object().reviewcomment_set.all().order_by("-pk"),
        }
    
class LikeDislikeReviewView(View):
    def post(self, request, *args, **kwargs):
        review = get_object_or_404(klass=Review, pk=self.kwargs.get("review_pk"))

        if request.POST.get("rating") == "like":
            like_dislike(request=request, action_to_do=review.reviewlike_set, action_to_delete=review.reviewdislike_set)
        elif request.POST.get("rating") == "dislike": 
            like_dislike(request=request, action_to_do=review.reviewdislike_set, action_to_delete=review.reviewlike_set)
        else:
            raise Http404
        
        return redirect(to="movies:review_path", slug=self.kwargs.get("slug"), pk=self.kwargs.get("pk"), review_pk=self.kwargs.get("review_pk"))
    
class AddCommentReviewView(View):
    def post(self, request, *args, **kwargs):
        form = ReviewCommentForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect(to="movies:review_path", slug=self.kwargs.get("slug"), pk=self.kwargs.get("pk"), review_pk=self.kwargs.get("review_pk"))
        
class StaffOfAMovieView(View):
    template_name = "movies/movie_staff.html"

    def dispatch(self, request, *args, **kwargs):
        self.movie = get_object_or_404(klass=Movie, slug=self.kwargs.get("slug"), pk=self.kwargs.get("pk"))    
        return super().dispatch(request, *args, **kwargs)
    
    def __get_jobs(self, job: str):
        try:
            return {
                "directors": (self.movie.directors.all().order_by("director__order"), "director",),
                "script": (self.movie.scripts.all().order_by("script__order"), "script",),
                "producers": (self.movie.producers.all().order_by("producer__order"), "producer",),
                "cast": (self.movie.casts.all().order_by("cast__order"), "cast",),
            }[job]
        except KeyError:
            raise Http404

    def get_context_data(self, **kwargs):
        return {
            "movie": self.movie,
            
            "job": self.__get_jobs(self.kwargs.get("job"))
        }
    
    def get(self, request, *args, **kwargs):
        return render(
            request=request,
            template_name=self.template_name,
            context=self.get_context_data()
        )
    