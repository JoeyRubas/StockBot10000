from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
 
User = get_user_model()

class NoPromptSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_auto_signup_allowed(self, request, sociallogin):
        return True  # bypasses any checks or prompts
    def requires_additional_signup(self, request, sociallogin):
        return False
    def pre_social_login(self, request, sociallogin):
         """
         Return True to skip the 'Sign Up' form entirely.
         Force AllAuth to auto-link the Google login to an existing user if
         the email already exists in the database, skipping any conflict form.
         """
         print("💡 pre_social_login triggered!", flush=True)
         # If the user is already logged in, do nothing
         if request.user.is_authenticated:
             return
 
         # If Google provides an email
         email = sociallogin.user.email
         if email:
             try:
                 # Look for a user with the same email
                 existing_user = User.objects.get(email=email)
                 # Link this social login to that existing user
                 sociallogin.connect(request, existing_user)
             except User.DoesNotExist:
                 # No existing user → AllAuth can auto-create one
                 pass