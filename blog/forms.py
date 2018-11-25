from django import forms
from .models import Post, Profile, Comment
from django.contrib.auth.models import User

class PostCreateForm(forms.ModelForm):
	class Meta:
		model = Post
		fields = (
				'title',
				'body',
				'status',
				'restrict_comment',
			)



class PostEditForm(forms.ModelForm):
	class Meta:
		model = Post
		fields = (
				'title',
				'body',
				'status',
				'restrict_comment',
			)


class UserLoginForm(forms.Form):
	username = forms.CharField(label="")
	password = forms.CharField(label="", widget=forms.PasswordInput)


class UserRegistrationForm(forms.ModelForm):
	password = forms.CharField(widget = forms.PasswordInput(attrs = {'placeholder': 'Enter Password Here..'}))
	confirm_password = forms.CharField(widget = forms.PasswordInput(attrs = {'placeholder': 'Confirm Password..'}))
	class Meta:
		model = User
		fields = {
			'username',
			'email',
			'first_name',
			'last_name',
		}

	def clean_confirm_pasword(self):
		password = self.clean_data_get('password')
		confirm_password = self.clean_data_get('confirm_password')
		if password != confirm_password:
			raise forms.ValidationError('Password Mismatch')
		return confirm_password



# for user profile
class UserEditForm(forms.ModelForm):
	class Meta:
		model = User 
		fields = {
			'username',
			'email',
			'first_name',
			'last_name',
		}


class ProfileEditForm(forms.ModelForm):
	class Meta:
		model = Profile 
		exclude = ('user',)



class CommentForm(forms.ModelForm):
	content = forms.CharField(label="", widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Text goeshere!!', 'rows': '4', 'cols': '50'}))
	class Meta:
		model = Comment
		fields = ('content',)
