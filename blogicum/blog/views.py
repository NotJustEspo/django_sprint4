from typing import Any
from django import http
from django.db import models
from django.db.models.query import QuerySet
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import ListView, UpdateView, CreateView, DeleteView, DetailView
from django.db.models import Count
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from blog.models import Category, Post, User, Comment
from .forms import PostForm, UserForm, CommentForm

PAGE_SIZE = 10


class HomePageListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = PAGE_SIZE

    def get_queryset(self) -> QuerySet[Any]:
        return Post.objects.select_related(
            'location',
            'category',
            'author',
        ).annotate(
            comment_count=Count('comments')
        ).filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
            ).order_by(
                '-pub_date',
            )


# def category_posts(request, category_slug):
#     template = 'blog/category.html'
#     category = get_object_or_404(
#         Category,
#         slug=category_slug,
#         is_published=True)
#     post_list = base_query().filter(
#         category=category,)
#     context = {'category': category,
#                'post_list': post_list}
#     return render(request, template, context)

# def base_query():
#     query_set = Post.objects.select_related(
#         'location',
#         'author',
#         'category'
#     ).filter(
#         is_published=True,
#         category__is_published=True,
#         pub_date__lte=timezone.now())
#     return query_set


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        queryset = Post.objects.select_related(
            'location',
            'category',
            'author'
        ).annotate(
            comment_count=Count('comments')
        ).filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        ).order_by('-pub_date')
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return super().get_queryset().filter()

    def get_context_data(self, **kwargs):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        context['category'] = category
        return super().get_context_data(**kwargs)

class ProfileListView(ListView):
    model = User
    form_class = UserForm
    template_name = 'blog/profile.html'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        self.author = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        context['profile'] = self.author
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(
            Post,
            id=kwargs['post_id'],
            author=request.user
        )
        if not request.user.is_authenticated:
            return reverse(
                'blog:post_detail',
                kwargs={'post_id': self.post_obj.id}
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.post = self.post_obj
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.post_obj.id})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(
            Post,
            id=kwargs['post_id'],)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post_id = self.kwargs['post_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.post_obj.id})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(
            Post,
            id=kwargs['post_id'],)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post_id = self.kwargs['post_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.post_obj.id}
            )


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(
            Post,
            id=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post_id = self.kwargs['post_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.post_obj.id}
            )


# def base_query():
#     query_set = Post.objects.select_related(
#         'location',
#         'author',
#         'category'
#     ).filter(
#         is_published=True,
#         category__is_published=True,
#         pub_date__lte=timezone.now())
#     return query_set


# def index(request):
#     template = 'blog/index.html'
#     post_list = base_query()[:PAGE_SIZE]
#     context = {'post_list': post_list}
#     return render(request, template, context)


# def post_detail(request, pk):
#     template = 'blog/detail.html'
#     post = get_object_or_404(base_query(), pk=pk)
#     context = {
#         'post': post,
#     }
#     return render(request, template, context)

