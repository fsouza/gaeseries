# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from forms import PostForm
from models import Post

@login_required
def new_post(request):
    form = PostForm()
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            return HttpResponseRedirect(reverse('core.views.list_posts'))
    return render_to_response('new_post.html',
            locals(), context_instance=RequestContext(request)
    )

def list_posts(request):
    posts = Post.objects.all()
    return render_to_response('list_posts.html',
            locals(), context_instance=RequestContext(request)
    )
