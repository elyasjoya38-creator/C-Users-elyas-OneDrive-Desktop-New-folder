from django.db import models


def user_role(request):
    if not hasattr(request, "user") or not request.user.is_authenticated:
        return {"user_role": "Guest"}

    groups = set(request.user.groups.values_list("name", flat=True))
    if request.user.is_staff or request.user.is_superuser or "Admin" in groups:
        role = "Admin"
    elif "Teacher" in groups:
        role = "Teacher"
    elif "Student" in groups:
        role = "Student"
    else:
        role = "User"
    return {"user_role": role}
