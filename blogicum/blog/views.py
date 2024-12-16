from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from .models import Post, Category, Comment
from .mixins import PostListMixin, ChangePostMixin, CommentChangeMixin
from .forms import PostForm, UserForm, CommentForm


PAGE_PAGINATOR = 10

User = get_user_model()


class IndexHome(PostListMixin, ListView):
    template_name = 'blog/index.html'

    def get_queryset(self):
        return super().get_queryset().filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        posts = self.model.objects.select_related(
            'location', 'category', 'author'
        )
        object = super().get_object(posts)
        if object.author != self.request.user:
            return get_object_or_404(
                posts.filter(
                    pub_date__lte=timezone.now(),
                    category__is_published=True,
                    is_published=True
                ),
                pk=self.kwargs['post_id']
            )
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class CategoryListView(PostListMixin, ListView):
    template_name = 'blog/category.html'

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return super().get_queryset().filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
            category=self.category
        )

    def get_context_data(self, **kwargs):
        contex = super().get_context_data(**kwargs)
        contex['category'] = self.category
        return contex


class ProfileView(PostListMixin, ListView):
    template_name = 'blog/profile.html'

    def get_queryset(self):
        self.author = get_object_or_404(
            User,
            username=self.kwargs['username'],
        )
        if self.author != self.request.user:
            return super().get_queryset().filter(
                is_published=True,
                category__is_published=True,
                author=self.author
            )
        return super().get_queryset().filter(
            author=self.author
        )

    def get_context_data(self, **kwargs):
        contex = super().get_context_data(**kwargs)
        contex['profile'] = self.author
        return contex


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user}
        )

    def get_object(self, queryset=None):
        return self.request.user


class CreatePostView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user}
        )


class PostUpdateView(LoginRequiredMixin, ChangePostMixin, UpdateView):
    form_class = PostForm

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class PostDeleteView(LoginRequiredMixin, ChangePostMixin, DeleteView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user}
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'post_id'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post, pk=self.kwargs.get('post_id')
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs.get('post_id')})


class CommentUpdateView(LoginRequiredMixin, CommentChangeMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(LoginRequiredMixin, CommentChangeMixin, DeleteView):
    """Удаление комментария."""
