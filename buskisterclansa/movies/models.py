# Django
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ObjectDoesNotExist

# My apps
from accounts.models import CustomUser
from genres.models import Genre
from movie_staff.models import MovieStaff
from companies.models import Company

# Movie
class Movie(models.Model):
    name = models.CharField(max_length=50, blank=False, null=False)
    slug = models.SlugField(max_length=50, editable=False, blank=False, null=False)
    year = models.DateField(default=timezone.now().date(), blank=False, null=False)
    synopsis = models.TextField(max_length=1000, blank=False, null=False)

    image = models.ImageField(blank=False, default=None)

    genres = models.ManyToManyField(to=Genre)

    directors = models.ManyToManyField(to=MovieStaff, through="Director", related_name="movie_director")
    casts = models.ManyToManyField(to=MovieStaff, through="Cast", related_name="movie_cast")
    producers = models.ManyToManyField(to=MovieStaff, through="Producer", related_name="movie_producer")
    scripts = models.ManyToManyField(to=MovieStaff, through="Script", related_name="movie_script")

    producer_companies = models.ManyToManyField(to=Company, related_name="as_producer")

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        self.slug = slugify(self.name)

        return super().save(*args, **kwargs)
    
    def get_stars_quantity(self, star: int):
        assert star <= 5 and star > 0, f" '{star}' is not a valid star"

        return len(self.review_set.filter(rate_by_stars=star))
    
    def get_reviews_quantity(self):
        return len(self.review_set.all())



class Cast(models.Model):
    movie = models.ForeignKey(to=Movie, on_delete=models.CASCADE)
    movie_staff = models.ForeignKey(to=MovieStaff, on_delete=models.CASCADE)

    order = models.IntegerField(default=0, blank=False, null=False)

    def __str__(self) -> str:
        return f"'{self.movie_staff.name}' as cast '{self.movie.name}'"
    
class Director(models.Model):
    movie = models.ForeignKey(to=Movie, on_delete=models.CASCADE)
    movie_staff = models.ForeignKey(to=MovieStaff, on_delete=models.CASCADE)

    order = models.IntegerField(default=0, blank=False, null=False)

    def __str__(self) -> str:
        return f"'{self.movie_staff.name}' as director of '{self.movie.name}'"

class Producer(models.Model):
    movie = models.ForeignKey(to=Movie, on_delete=models.CASCADE)
    movie_staff = models.ForeignKey(to=MovieStaff, on_delete=models.CASCADE)

    order = models.IntegerField(default=0, blank=False, null=False)

    def __str__(self) -> str:
        return f"'{self.movie_staff.name}' as producer of '{self.movie.name}'"

class Script(models.Model):
    movie = models.ForeignKey(to=Movie, on_delete=models.CASCADE)
    movie_staff = models.ForeignKey(to=MovieStaff, on_delete=models.CASCADE)

    order = models.IntegerField(default=0, blank=False, null=False)

    def __str__(self) -> str:
        return f"'{self.movie_staff.name}' as script of '{self.movie.name}'"

# Reviews    
class Review(models.Model):
    movie = models.ForeignKey(to=Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(to=CustomUser, on_delete=models.PROTECT)

    name = models.CharField(max_length=30, null=False, blank=False)
    slug = models.SlugField(max_length=30, null=False, blank=False, editable=False)
    content = models.TextField(max_length=2600, null=False, blank=False)
    pub_date = models.DateTimeField(default=timezone.now(), null=False, blank=False)

    rate_by_stars = models.IntegerField(choices=((1,1,),(2,2,),(3,3,),(4,4,),(5,5,),), null=False, blank=False)

    def __str__(self) -> str:
        return self.name
    
    def save(self, *args, **kwargs) -> None:
        self.slug = slugify(self.name)

        return super().save(*args, **kwargs)

    def has_like_or_dislike(self, option: int, user_pk):
        """
        option 1 = like
        option 2 = dislike
        any other, Error...
        """

        options = {
            1: self.reviewlike_set,
            2: self.reviewdislike_set,
        }

        try:
            options[option].get(user__pk=user_pk)
            return True
        except ObjectDoesNotExist:
            return False

class ReviewLike(models.Model):
    review = models.ForeignKey(to=Review, on_delete=models.CASCADE)
    user = models.ForeignKey(to=CustomUser, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.username} likes '{self.review.name}'"
    
class ReviewDislike(models.Model):
    review = models.ForeignKey(to=Review, on_delete=models.CASCADE)
    user = models.ForeignKey(to=CustomUser, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.username} dislikes '{self.review.name}'"
    
class ReviewComment(models.Model):
    review = models.ForeignKey(to=Review, on_delete=models.CASCADE)
    user = models.ForeignKey(to=CustomUser, on_delete=models.CASCADE)

    content = models.TextField(max_length=300, null=False, blank=False,)
