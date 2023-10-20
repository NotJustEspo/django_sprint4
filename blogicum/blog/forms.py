from django import forms
from .models import Post, Comment, User


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%d-%m-%Y %H:%M'),
            'text': forms.Textarea({'rows': '3'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        exclude = ('post', 'author',)
        widgets = {
            'text': forms.Textarea({'rows': '3'}),
        }


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'
