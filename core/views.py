from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse


def logout_view(request):
    logout(request)
    # Redirect to a desired page after logout (e.g., the login page)
    return redirect(reverse("admin:login"))
