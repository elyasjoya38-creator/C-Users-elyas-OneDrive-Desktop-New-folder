from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import addpdcform
from .models import pdc_detials


def is_pdc_admin(user):
    """Only staff/superusers may manage PDC records."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


admin_required = user_passes_test(is_pdc_admin, login_url="user_dashboard")


@login_required
def home(request):
    if not is_pdc_admin(request.user):
        return redirect("user_dashboard")
    today = timezone.localdate()
    records = pdc_detials.objects.all()
    return render(request, "enroll/index.html", {
        "active_page": "home", "total_pdcs": records.count(),
        "seminar_count": records.filter(types="Seminar").count(),
        "workshop_count": records.filter(types="Workshop").count(),
        "upcoming_pdcs": records.filter(startdate__gte=today).count(),
        "recent_pdcs": records.order_by("-id")[:5],
    })


@login_required
def user_dashboard(request):
    if is_pdc_admin(request.user):
        return redirect("home")
    return render(request, "enroll/user_dashboard.html", {"active_page": "user_dashboard"})


@admin_required
def pdcadd(request):
    form = addpdcform(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "PDC successfully added.")
        return redirect("managepdc")
    if request.method == "POST":
        messages.error(request, "Please correct the errors below.")
    return render(request, "enroll/addpdc.html", {"form": form, "active_page": "addpdc"})


@admin_required
def managepdc(request):
    records = pdc_detials.objects.all().order_by("-id")
    return render(request, "enroll/managepdc.html", {
        "data": records, "records": records, "active_page": "managepdc"
    })


@admin_required
def updatepdc(request, id):
    record = get_object_or_404(pdc_detials, pk=id)
    form = addpdcform(request.POST or None, instance=record)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "PDC successfully updated.")
        return redirect("managepdc")
    if request.method == "POST":
        messages.error(request, "Please correct the errors below.")
    return render(request, "enroll/updatepdc.html", {
        "form": form, "data": record, "active_page": "managepdc"
    })


@admin_required
@require_POST
def deletes(request, id):
    record = get_object_or_404(pdc_detials, pk=id)
    record.delete()
    messages.success(request, "PDC successfully deleted.")
    return redirect("managepdc")


def user_register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        # Public registration must never grant staff/admin privileges.
        user.is_staff = False
        user.is_superuser = False
        user.save()
        messages.success(request, "Your account was created. Please sign in.")
        return redirect("login")
    return render(request, "enroll/register.html", {"form": form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next", "")
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url, allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                # Do not let normal users redirect into staff-only destinations.
                if is_pdc_admin(user) or next_url not in ("/addpdc/", "/managepdc/"):
                    return redirect(next_url)
            return redirect("home")
        messages.error(request, "Username or password is incorrect.")
    return render(request, "enroll/login.html")


@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")
