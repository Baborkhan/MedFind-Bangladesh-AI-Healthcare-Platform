"""
MedFind — Authentication & Account Views
Role-based login: patient | doctor | hospital_admin | pharmacy_admin | lab_admin | superadmin
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone
from .models import User


def make_token(user) -> dict:
    """Issue JWT access + refresh token pair for a User instance."""
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["full_name"] = user.full_name
    return {
        "access":  str(refresh.access_token),
        "refresh": str(refresh),
    }


def get_user(request) -> User | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        uid = int(auth.replace("Bearer ", "").split("_")[2])
        return User.objects.get(pk=uid, is_active=True)
    except Exception:
        return None


# ─── Role → Dashboard redirect map ─────────────────────────────
ROLE_DASHBOARDS = {
    "superadmin":     "/pages/admin/dashboard.html",
    "hospital_admin": "/pages/hospital/admin.html",
    "pharmacy_admin": "/pages/billing/pharmacy.html",
    "lab_admin":      "/pages/lab/admin.html",
    "doctor":         "/pages/doctors/console.html",
    "patient":        "/pages/patients/dashboard.html",
}


class RegisterView(APIView):
    permission_classes = []

    def post(self, request):
        data = request.data
        required = ["email", "password", "full_name"]
        for f in required:
            if not data.get(f):
                return Response({"success": False, "message": f"{f} is required"}, status=400)

        if User.objects.filter(email=data["email"].lower()).exists():
            return Response({"success": False, "message": "Email already registered"}, status=409)

        allowed_roles = ("patient", "doctor")
        role = data.get("role", "patient")
        if role not in allowed_roles:
            role = "patient"  # Default — other roles created by superadmin only

        user = User.objects.create_user(
            email=data["email"].lower(),
            password=data["password"],
            full_name=data["full_name"],
            phone=data.get("phone", ""),
            role=role,
        )
        token = make_token(user)
        return Response({
            "success": True,
            "message": "Registration successful",
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "role_display": user.role_display,
                "dashboard": ROLE_DASHBOARDS.get(user.role, "/"),
            }
        }, status=201)


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        email    = request.data.get("email", "").lower().strip()
        password = request.data.get("password", "")

        if not email or not password:
            return Response({"success": False, "message": "Email and password required"}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"success": False, "message": "Invalid email or password"}, status=401)

        if not user.check_password(password):
            return Response({"success": False, "message": "Invalid email or password"}, status=401)

        if not user.is_active:
            return Response({"success": False, "message": "Account is deactivated. Contact support."}, status=403)

        token = make_token(user)
        return Response({
            "success": True,
            "message": f"Welcome back, {(user.full_name.split() or [user.email.split('@')[0]])[0]}!",
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "role_display": user.role_display,
                "is_verified": user.is_verified,
                "date_joined": user.date_joined.isoformat(),
                "loyalty_points": user.loyalty_points,
                "dashboard": ROLE_DASHBOARDS.get(user.role, "/"),
            }
        })


class ProfileView(APIView):
    def get(self, request):
        user = get_user(request)
        if not user:
            return Response({"success": False, "message": "Unauthorized"}, status=401)
        return Response({
            "success": True,
            "data": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "role": user.role,
                "role_display": user.role_display,
                "is_verified": user.is_verified,
                "date_joined": user.date_joined.isoformat(),
                "loyalty_points": user.loyalty_points,
                "dashboard": ROLE_DASHBOARDS.get(user.role, "/"),
            }
        })

    def put(self, request):
        user = get_user(request)
        if not user:
            return Response({"success": False, "message": "Unauthorized"}, status=401)
        allowed = ["full_name", "phone"]
        for f in allowed:
            if f in request.data:
                setattr(user, f, request.data[f])
        if "new_password" in request.data:
            if not request.data.get("current_password"):
                return Response({"success": False, "message": "current_password required"}, status=400)
            if not user.check_password(request.data["current_password"]):
                return Response({"success": False, "message": "Current password incorrect"}, status=400)
            user.set_password(request.data["new_password"])
        user.save()
        return Response({"success": True, "message": "Profile updated"})


class AdminCreateStaffView(APIView):
    """Superadmin creates hospital_admin / pharmacy_admin / lab_admin accounts."""
    def post(self, request):
        user = get_user(request)
        if not user or user.role != "superadmin":
            return Response({"success": False, "message": "Superadmin only"}, status=403)

        allowed_staff_roles = ("hospital_admin", "pharmacy_admin", "lab_admin", "doctor")
        role = request.data.get("role", "hospital_admin")
        if role not in allowed_staff_roles:
            return Response({"success": False, "message": f"Invalid role. Choose from {allowed_staff_roles}"}, status=400)

        email = request.data.get("email", "").lower()
        if not email or not request.data.get("password") or not request.data.get("full_name"):
            return Response({"success": False, "message": "email, password, full_name required"}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"success": False, "message": "Email already registered"}, status=409)

        staff = User.objects.create_user(
            email=email,
            password=request.data["password"],
            full_name=request.data["full_name"],
            phone=request.data.get("phone", ""),
            role=role,
            is_verified=True,
        )
        return Response({
            "success": True,
            "message": f"{role.replace('_',' ').title()} account created",
            "data": {"id": staff.id, "email": staff.email, "role": staff.role}
        }, status=201)


class UserListView(APIView):
    """Superadmin: list all users with role filter."""
    def get(self, request):
        user = get_user(request)
        if not user or user.role != "superadmin":
            return Response({"success": False, "message": "Superadmin only"}, status=403)
        role_filter = request.query_params.get("role")
        qs = User.objects.all().order_by("-date_joined")
        if role_filter:
            qs = qs.filter(role=role_filter)
        page = max(1, int(request.query_params.get("page", 1)))
        limit = min(100, int(request.query_params.get("limit", 20)))
        total = qs.count()
        qs = qs[(page-1)*limit:page*limit]
        return Response({
            "success": True,
            "total": total, "page": page,
            "data": [{"id": u.id, "email": u.email, "full_name": u.full_name,
                      "role": u.role, "is_active": u.is_active,
                      "date_joined": u.date_joined.isoformat()} for u in qs]
        })

class DoctorRegisterView(APIView):
    """Register a doctor account — requires admin approval before activation."""
    permission_classes = []

    def post(self, request):
        data = request.data
        required = ["email", "password", "full_name"]
        for f in required:
            if not data.get(f):
                return Response({"success": False, "message": f"{f} is required"}, status=400)

        if User.objects.filter(email=data["email"].lower()).exists():
            return Response({"success": False, "message": "Email already registered"}, status=409)

        user = User.objects.create_user(
            email=data["email"].lower(),
            password=data["password"],
            full_name=data["full_name"],
            phone=data.get("phone", ""),
            role="doctor",
            is_active=False,  # Requires admin approval
            is_verified=False,
        )
        return Response({
            "success": True,
            "message": "Doctor registration submitted. Your account will be reviewed by an admin.",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "status": "pending_approval",
            }
        }, status=201)


class HospitalRegisterView(APIView):
    """Register a hospital admin account — requires admin approval."""
    permission_classes = []

    def post(self, request):
        data = request.data
        required = ["email", "password", "full_name"]
        for f in required:
            if not data.get(f):
                return Response({"success": False, "message": f"{f} is required"}, status=400)

        if User.objects.filter(email=data["email"].lower()).exists():
            return Response({"success": False, "message": "Email already registered"}, status=409)

        user = User.objects.create_user(
            email=data["email"].lower(),
            password=data["password"],
            full_name=data["full_name"],
            phone=data.get("phone", ""),
            role="hospital_admin",
            is_active=False,  # Requires admin approval
            is_verified=False,
        )
        return Response({
            "success": True,
            "message": "Hospital registration submitted. Your account will be reviewed by an admin.",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "status": "pending_approval",
            }
        }, status=201)


class SendEmailOTPView(APIView):
    """Send OTP via email for registration verification — alias for otp_auth send-otp."""
    permission_classes = []

    def post(self, request):
        from otp_auth.services import send_otp
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response({"success": False, "message": "Email is required"}, status=400)
        result = send_otp(email)
        status_code = 200 if result["success"] else (429 if result.get("seconds_left") else 400)
        return Response(result, status=status_code)
