from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db import transaction
from subscriptions.services.subscription_service import assign_free_plan
from .models import User


def sign_up(request: HttpRequest):
    if request.method == "POST":
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        national_id = request.POST.get("national_id")
        mobile = request.POST.get("mobile")
        date_of_birth = request.POST.get("date_of_birth")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # التحقق من كلمة المرور
        if password != confirm_password:
            messages.error(request, "كلمة المرور غير متطابقة", "alert-danger")
            return render(request, "accounts/signup.html")

        # التحقق من الإيميل
        if User.objects.filter(email=email).exists():
            messages.error(request, "البريد الإلكتروني مستخدم مسبقاً", "alert-danger")
            return render(request, "accounts/signup.html")

        # التحقق من الهوية
        if User.objects.filter(national_id=national_id).exists():
            messages.error(request, "رقم الهوية مستخدم مسبقاً", "alert-danger")
            return render(request, "accounts/signup.html")

        # إنشاء المستخدم
        with transaction.atomic():
         user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            national_id=national_id,
            mobile=mobile,
            date_of_birth=date_of_birth or None,
        )

        assign_free_plan(user)  # Assign the Free plan to the new user
        login(request, user)
        messages.success(request, "تم إنشاء الحساب بنجاح", "alert-success")
        return redirect("dashboard:home")

    return render(request, "accounts/signup.html")


def sign_in(request: HttpRequest):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            messages.success(request, "مرحباً بك!", "alert-success")
            return redirect(request.GET.get("next", "dashboard:home"))
        else:
            messages.error(request, "البريد الإلكتروني أو كلمة المرور غير صحيحة", "alert-danger")

    return render(request, "accounts/signin.html")


def log_out(request: HttpRequest):
    logout(request)
    messages.success(request, "تم تسجيل الخروج بنجاح", "alert-warning")
    return redirect("accounts:sign_in")
