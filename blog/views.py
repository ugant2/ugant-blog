from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from .models import Post, Profile, Images, Comment
from .forms import * 
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.template.loader import render_to_string # for ajax loder
from django.forms import modelformset_factory
from django.contrib import messages


# Create your views here.

def post_list(request):
	# posts = Post.objects.all()
	post_list = Post.published.all().order_by('-id') # we have used model manager, it wont show drafted post to user.
	query = request.GET.get('q')
	# print(query)
	if query:
		post_list = Post.published.filter(
			Q(title__icontains=query)|
			Q(author__username=query)|
			Q(body__icontains=query)
			)
	# for oaginatior
	paginator = Paginator(post_list, 5)
	page = request.GET.get('page')
	try:
		posts = paginator.page(page)
	except PageNotAnInteger:
		posts = paginator.page(1)
	except EmptyPage:
		posts = paginator.page(paginator.num_pages)


	if page is None:
		start_index = 0
		end_index = 7
	else:
		(start_index, end_index) = proper_pagination(posts, index=4)

	page_range = list(paginator.page_range)[start_index:end_index]
	# [1,2,3,4,6,7][0:7]

	context = {
		'posts': posts,
		'page_range': page_range,
	}
	return render(request, 'blog/post_list.html', context)


def proper_pagination(posts, index):
	start_index = 0
	end_index = 7
	if posts.number > index:
		start_index = posts.number - index
		end_index = start_index + end_index
	return (start_index, end_index)




# option 1
# def post_detail(request, id, slug):
# 	post = Post.objects.get(id=id)
# 	context = {
# 		'post': post
# 	}
# 	return render(request, 'blog/post_detail.html', context)

# option 2 uing get_object_or_404
def post_detail(request, id, slug):
	post = get_object_or_404(Post, id=id, slug=slug) # will give 404 error page if post is not found
	comments = Comment.objects.filter(post=post, reply=None).order_by('-id')
	is_liked = False
	is_favourite = False

	if post.likes.filter(id=request.user.id).exists():
		is_liked = True

	if post.favourite.filter(id=request.user.id).exists():
		is_favourite = True

	if request.method == 'POST':
		comment_form = CommentForm(request.POST or None)
		if comment_form.is_valid():
			content = request.POST.get('content')
			reply_id = request.POST.get('comment_id')
			comment_qs = None		
			if reply_id:
				comment_qs = Comment.objects.get(id=reply_id)
			comment = Comment.objects.create(post=post, user=request.user, content=content, reply=comment_qs)
			comment.save()
			# return HttpResponseRedirect(post.get_absolute_url())
	else:
		comment_form = CommentForm()

	context = {
		'post': post,
		'is_liked': is_liked,
		'is_favourite': is_favourite,
		'total_likes': post.total_likes(),
		'comments': comments,
		'comment_form': comment_form,	
	}
	# for using ajax
	if request.is_ajax():
		html = render_to_string('blog/comments.html', context, request=request)
		return JsonResponse({'form': html})
	return render(request, 'blog/post_detail.html', context)


# favourite list
def favourite_post_list(request):
	user = request.user
	favourite_posts = user.favourite.all()
	context = {
		'favourite_posts': favourite_posts,
	}
	return render(request, 'blog/post_favourite_list.html', context)



# favourite post
def favourite_post(request, id):
	post = get_object_or_404(Post, id=id)
	if post.favourite.filter(id=request.user.id).exists():
		post.favourite.remove(request.user)
	else:
		post.favourite.add(request.user)
	return HttpResponseRedirect(post.get_absolute_url())



def like_post(request):
	# post = get_object_or_404(Post, id=request.POST.get('post_id'))
	post = get_object_or_404(Post, id=request.POST.get('id'))
	is_liked = False
	if post.likes.filter(id=request.user.id).exists():
		post.likes.remove(request.user)
		is_like = False
	else:
		post.likes.add(request.user)
		is_like = True
	context = {
		'post': post,
		'is_liked': is_liked,
		'total_likes': post.total_likes(),
	}
	# return HttpResponseRedirect(post.get_absolute_url())
	if request.is_ajax():
		html = render_to_string('blog/like_section.html', context, request=request)
		return JsonResponse({'form': html})



def post_create(request):
	ImageFormset = modelformset_factory(Images, fields=('image',), extra=4)
	if request.method == 'POST':
		form = PostCreateForm(request.POST)
		formset = ImageFormset(request.POST or None, request.FILES or None)
		if form.is_valid() and formset.is_valid():
			post = form.save(commit=False)
			post.author = request.user
			post.save()

			for f in formset:
				try:
					photo = Images(post=post, image=f.cleaned_data['image'])
					photo.save()
				except Exception as e:
					break
			# for django message framework
			messages.success(request, "Post has been successfully created.")

			return redirect('post_list') # it return post_list view

	else:
		form = PostCreateForm() # by default POSTCreateForm is get method
		formset = ImageFormset(queryset=Images.objects.none())

	context = {
		'form': form,
		'formset': formset,
	}
	return render(request, 'blog/post_create.html', context)



# for post editing
def post_edit(request, id):
	post = get_object_or_404(Post, id=id)
	ImageFormset = modelformset_factory(Images, fields=('image',), extra=4, max_num=4)
	if post.author != request.user:
		raise Http404("Please Login to update your post, thank you!!")
	if request.method == "POST":
		form = PostEditForm(request.POST or None, instance=post) # it will create form in Post edit page
		formset = ImageFormset(request.POST or None, request.FILES or None)
		if form.is_valid() and formset.is_valid():
			form.save()
			print(formset.cleaned_data)
			data = Images.objects.filter(post=post)

			for index, f in enumerate(formset):
				if f.cleaned_data:
					if f.cleaned_data['id'] is None:
						photo = Images(post=post, image=f.cleaned_data.get('image'))
						photo.save()
					elif f.cleaned_data['image'] is False:
						photo = Images.objects.get(id=request.POST.get('form-' + str(index) + '-id'))
						photo.delete()
					else:
						photo = Images(post=post, image=f.cleaned_data.get('image'))
						d = Images.objects.get(id=data[index].id)
						d.image = photo.image
						d.save()
			# for django message framework
			messages.success(request, "{} has been successfully updated!".format(post.title))
			return HttpResponseRedirect(post.get_absolute_url())
	else:
		form = PostEditForm(instance=post)
		formset = ImageFormset(queryset=Images.objects.filter(post=post)) # queryset is used cause it will display images uploded by author
	context = {
		'form': form,
		'post': post,
		'formset': formset,
	}
	return render(request, 'blog/post_edit.html', context)




# For post delete
def post_delete(request, id):
	post = get_object_or_404(Post, id=id)
	if request.user != post.author:
		raise Http404()
	post.delete()
	# for django message framework
	messages.warning(request, 'post has been successfully deleted!')
	return redirect('post_list')






def user_login(request):
	if request.method == 'POST':
		form = UserLoginForm(request.POST)
		if form.is_valid():
			username = request.POST['username']
			password = request.POST['password']
			user = authenticate(username=username, password=password)
			if user:
				if user.is_active:
					login(request, user)
					return HttpResponseRedirect(reverse('post_list'))
				else:
					return HttpResponse("User is not active")
			else:
				return HttpResponse("User is None")
	else:
		form = UserLoginForm()

	context = {
		'form': form,
	}
	return render(request, 'blog/login.html', context)


def user_logout(request):
	logout(request)
	return redirect('post_list')
	# return HttpResponseRedirect(reverse('post_list'))


def register(request):
	if request.method == 'POST':
		form = UserRegistrationForm(request.POST or None)
		if form.is_valid():
			new_user = form.save(commit=False)
			new_user.set_password(form.cleaned_data['password'])
			new_user.save()
			Profile.objects.create(user=new_user) # it will create empty profile of the user
			return redirect('post_list')

	else:
		form = UserRegistrationForm()
	context = {
		'form': form
	}
	return render(request, 'registration/register.html', context)



@login_required
def edit_profile(request):
	if request.method == 'POST':
		user_form = UserEditForm(data=request.POST or None, instance=request.user)
		profile_form = ProfileEditForm(data=request.POST or None, instance=request.user.profile, files=request.FILES)
		if user_form.is_valid() and profile_form.is_valid():
			user_form.save()
			profile_form.save()
	else:
		user_form = UserEditForm(instance=request.user)
		profile_form = ProfileEditForm(instance=request.user.profile)

	context = {
		'user_form': user_form,
		'profile_form': profile_form,
	}	
	return render(request, 'blog/edit_profile.html', context)

