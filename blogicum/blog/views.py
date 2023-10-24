from typing import Any
from django import http
from django.db import models
from blogicum.settings import PAGE_SIZE
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,)
from django.http import Http404, HttpResponse

from blog.models import Category, Comment, Post, User
from .forms import CommentForm, PostForm, UserForm


class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'


class PostDispatchMixin:

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(
            Post,
            id=kwargs['post_id'])
        if self.post_obj.author != request.user:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)


class CommentMixin:
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'


def get_default_queryset(query_filter, query_annotate):
    queryset = Post.objects.select_related(
        'location',
        'category',
        'author'
    )
    if query_filter:
        queryset = queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )
    if query_annotate:
        queryset = queryset.annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    return queryset


class HomePageListView(ListView):
    """VIEW-класс главной страницы"""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        return get_default_queryset(True, True)


class CategoryListView(ListView):
    """VIEW-класс страницы категорий"""

    model = Category
    template_name = 'blog/category.html'
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return get_default_queryset(
            False,
            True).filter(
                category__slug=self.kwargs['category_slug'],
                is_published=True,
                pub_date__lte=timezone.now()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileListView(ListView):
    """VIEW-класс страницы профиля"""

    model = Post
    template_name = 'blog/profile.html'
    slug_url_kwarg = 'username'
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        self.user = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        if self.user == self.request.user:
            return get_default_queryset(
                False,
                True).filter(
                    author=self.user
            )
        return get_default_queryset(
            True,
            True).filter(
                author=self.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.user
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """VIEW-класс редактирования профиля пользователя"""

    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user})


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    """VIEW-класс создания поста"""

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user})


class PostDetailView(DetailView):
    """VIEW-класс подробной информации о посте"""

    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        return get_default_queryset(False, False)

    def get_object(self):
        post = super().get_object()
        if not (self.request.user == post.author) and \
            (post.is_published is False
             or post.category.is_published is False
                or post.pub_date > timezone.now()):
            raise Http404
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostUpdateView(PostDispatchMixin, LoginRequiredMixin, PostMixin, UpdateView):
    """VIEW-класс редактирования поста"""

    pk_url_kwarg = 'post_id'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.post_obj.id})


class PostDeleteView(PostDispatchMixin, LoginRequiredMixin, PostMixin, DeleteView):
    """VIEW-класс удаления поста"""

    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.post_obj)
        return context

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user})


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):
    """VIEW-класс создания комментария к посту"""

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


class CommentUpdateView(LoginRequiredMixin, CommentMixin, UpdateView):
    """VIEW-класс редактирования комментария"""

    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Comment,
            id=kwargs['comment_id'],
            post=kwargs['post_id'])
        if instance.author != request.user:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']})


class CommentDeleteView(LoginRequiredMixin, CommentMixin, DeleteView):
    """VIEW-класс удаления комментария"""

    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Comment,
            id=kwargs['comment_id'])
        if instance.author != request.user:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['comment_id']}
        )
