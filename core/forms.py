from models import Post
from django import forms

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('user',)

    def save(self, user, commit = True):
        post = super(PostForm, self).save(commit = False)
        post.user = user

        if commit:
            post.save()

        return post

