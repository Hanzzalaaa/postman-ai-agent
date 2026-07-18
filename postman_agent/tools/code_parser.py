import ast
import re
from typing import Any


# ── Folder keyword map (order matters — more specific first) ──────────────────
_FOLDER_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Authentication", ["auth", "login", "logout", "register", "signup", "signin", "token",
                        "refresh", "password", "forgot", "reset", "verify", "otp", "2fa",
                        "session", "credential", "oauth"]),
    ("Profile",        ["profile", "profiles", "me", "myself", "avatar", "bio"]),
    ("Users",          ["user", "users", "account", "accounts", "member", "members",
                        "subscriber", "subscribers", "customer", "customers"]),
    ("Products",       ["product", "products", "item", "items", "inventory", "catalogue",
                        "catalog", "listing", "listings", "goods", "merchandise", "sku"]),
    ("Orders",         ["order", "orders", "purchase", "purchases", "booking", "bookings",
                        "reservation", "reservations", "transaction", "transactions"]),
    ("Payments",       ["payment", "payments", "pay", "stripe", "paypal", "billing",
                        "invoice", "invoices", "checkout", "charge", "charges",
                        "subscription", "subscriptions", "wallet", "refund", "refunds"]),
    ("Cart",           ["cart", "basket", "bag", "trolley"]),
    ("Wishlist",       ["wishlist", "favorites", "favourite", "saved", "bookmark"]),
    ("Categories",     ["category", "categories", "tag", "tags", "label", "labels",
                        "genre", "genres", "collection", "collections",
                        "type", "types"]),  # type/types before Health
    ("Reviews",        ["review", "reviews", "rating", "ratings", "feedback", "feedbacks",
                        "comment", "comments", "testimonial", "testimonials"]),
    ("Addresses",      ["address", "addresses", "location", "locations", "destination"]),
    ("Shipping",       ["shipping", "shipment", "shipments", "delivery", "track", "tracking",
                        "courier", "dispatch"]),
    ("Notifications",  ["notification", "notifications", "notify", "alert", "alerts",
                        "message", "messages", "inbox", "push"]),
    ("Uploads",        ["upload", "uploads", "media", "file", "files", "image", "images",
                        "photo", "photos", "video", "videos", "document", "documents",
                        "attachment", "attachments", "asset", "assets"]),
    ("Admin",          ["admin", "dashboard", "manage", "management", "cms", "panel",
                        "backoffice", "back-office", "superuser", "staff"]),
    ("Reports",        ["report", "reports", "analytics", "stats", "statistics",
                        "metric", "metrics", "insight", "insights", "export"]),
    ("Search",         ["search", "find", "filter", "query", "lookup", "explore", "discover"]),
    ("Coupons",        ["coupon", "coupons", "discount", "discounts", "promo", "promos",
                        "voucher", "vouchers", "offer", "offers", "deal", "deals"]),
    ("Health",         ["health", "ping", "heartbeat", "alive", "ready"]),
]

_VERSION_RE = re.compile(r'^v\d+$', re.IGNORECASE)
_STRIP_PREFIXES = {"api", "api-docs", "v1", "v2", "v3", "v4"}


def detect_auth_type(code: str) -> str:
    c = code.lower()
    if "jwt" in c or "jsonwebtoken" in c:
        return "JWT"
    if "oauth" in c or "passport" in c:
        return "OAuth"
    if "api_key" in c or "x-api-key" in c:
        return "API Key"
    return "JWT"


def detect_folder(path: str) -> str:
    parts = [p for p in path.split("/")
             if p and not p.startswith(":") and not p.startswith("{") and not p.startswith("<")]
    if not parts:
        return "General"
    while parts and (parts[0].lower() in _STRIP_PREFIXES or _VERSION_RE.match(parts[0])):
        parts = parts[1:]
    if not parts:
        return "General"
    full = "/".join(parts).lower()
    # Match against each segment individually first (more precise), then full path
    for segment in parts:
        seg = segment.lower()
        for folder, keywords in _FOLDER_KEYWORDS:
            if seg in keywords:
                return folder
    for folder, keywords in _FOLDER_KEYWORDS:
        if any(kw in full for kw in keywords):
            return folder
    return parts[0].replace("-", " ").replace("_", " ").title()


def generate_name(method: str, path: str) -> str:
    path_lower = path.lower()
    # strip dynamic segments for resource detection
    parts = [p for p in path.split("/")
             if p and not p.startswith(":") and not p.startswith("{") and not p.startswith("<")]
    while parts and (parts[0].lower() in _STRIP_PREFIXES or _VERSION_RE.match(parts[0])):
        parts = parts[1:]

    has_id_param = bool(re.search(r'(:[^/]+|\{[^}]+\}|<[^>]+>)$', path))

    if method == "GET":
        if "me" in path_lower and "profile" not in path_lower:
            return "Get Current User"
        if "health" in path_lower or "ping" in path_lower or "heartbeat" in path_lower:
            return "Health Check"
        if "tracking" in path_lower:
            return "Get Order Tracking"
        if "summary" in path_lower:
            return "Get Summary"
        if "search" in path_lower or "find" in path_lower:
            return "Search"
        if has_id_param:
            resource = (parts[-2] if len(parts) >= 2 else parts[-1]) if parts else "Resource"
            return f"Get {_humanize(resource)} By ID"
        resource = parts[-1] if parts else "Resource"
        return f"Get All {_humanize(resource)}"

    if method == "POST":
        if "login" in path_lower or "signin" in path_lower:
            return "Login User"
        if "register" in path_lower or "signup" in path_lower:
            return "Register User"
        if "logout" in path_lower:
            return "Logout User"
        if "refresh" in path_lower:
            return "Refresh Token"
        if "forgot" in path_lower:
            return "Forgot Password"
        if "reset" in path_lower:
            return "Reset Password"
        if "verify" in path_lower or "otp" in path_lower:
            return "Verify OTP"
        if "intent" in path_lower:
            return "Create Payment Intent"
        if "checkout" in path_lower or "session" in path_lower:
            return "Create Checkout Session"
        if "webhook" in path_lower:
            return "Payment Webhook"
        if "validate" in path_lower:
            return "Validate Coupon"
        if "upload" in path_lower:
            return "Upload File"
        resource = parts[-1] if parts else "Resource"
        return f"Create {_humanize(resource)}"

    if method == "PUT":
        resource = (parts[-2] if has_id_param and len(parts) >= 2 else parts[-1]) if parts else "Resource"
        return f"Update {_humanize(resource)}"

    if method == "PATCH":
        if "password" in path_lower:
            return "Change Password"
        if "status" in path_lower:
            resource = parts[-3] if len(parts) >= 3 else (parts[-2] if len(parts) >= 2 else "Item")
            return f"Update {_humanize(resource)} Status"
        if "restore" in path_lower:
            return "Restore Item"
        if "approve" in path_lower:
            return "Approve Item"
        resource = (parts[-2] if has_id_param and len(parts) >= 2 else parts[-1]) if parts else "Resource"
        return f"Partial Update {_humanize(resource)}"

    if method == "DELETE":
        resource = (parts[-2] if has_id_param and len(parts) >= 2 else parts[-1]) if parts else "Resource"
        return f"Delete {_humanize(resource)}"

    resource = parts[-1] if parts else "Resource"
    return f"{method.title()} {_humanize(resource)}"


def _humanize(s: str) -> str:
    return s.replace("-", " ").replace("_", " ").title()


def generate_body(path: str, method: str) -> dict | None:
    if method in ("GET", "DELETE"):
        return None
    p = path.lower()

    if "login" in p or "signin" in p:
        return {"email": "john@example.com", "password": "SecurePass123!"}
    if "register" in p or "signup" in p:
        return {"name": "John Doe", "email": "john@example.com",
                "password": "SecurePass123!", "confirmPassword": "SecurePass123!"}
    if "forgot" in p:
        return {"email": "john@example.com"}
    if "reset" in p and "password" in p:
        return {"token": "{{reset_token}}", "newPassword": "NewPass123!", "confirmPassword": "NewPass123!"}
    if ("change" in p and "password" in p) or re.search(r'profile.*/password', p):
        return {"currentPassword": "OldPass123!", "newPassword": "NewPass123!"}
    if "verify" in p or "otp" in p:
        return {"otp": "123456", "email": "john@example.com"}
    if "refresh" in p:
        return {"refreshToken": "{{refresh_token}}"}
    if "logout" in p:
        return {"refreshToken": "{{refresh_token}}"}
    if "webhook" in p:
        return {"event": "payment.succeeded", "data": {"object": {"amount": 9999}}}
    if "intent" in p:
        return {"amount": 9999, "currency": "usd", "paymentMethodId": "pm_card_visa"}
    if "checkout" in p or "session" in p:
        return {"items": [{"productId": "{{product_id}}", "quantity": 1}],
                "successUrl": "https://example.com/success",
                "cancelUrl": "https://example.com/cancel"}
    if any(x in p for x in ["payment", "pay", "stripe", "billing", "charge"]):
        return {"amount": 9999, "currency": "usd", "paymentMethodId": "pm_card_visa"}
    if any(x in p for x in ["product", "item", "inventory", "listing", "sku"]):
        return {"name": "Premium Laptop", "description": "High-performance laptop",
                "price": 999.99, "category": "{{category_id}}",
                "stock": 100, "images": ["https://example.com/image.jpg"], "sku": "LAP-001"}
    if any(x in p for x in ["order", "purchase", "booking"]):
        return {"items": [{"productId": "{{product_id}}", "quantity": 2}],
                "shippingAddressId": "{{address_id}}",
                "paymentMethod": "card", "couponCode": "SAVE10"}
    if any(x in p for x in ["cart", "basket", "bag"]):
        return {"productId": "{{product_id}}", "quantity": 1}
    if any(x in p for x in ["review", "rating", "feedback"]):
        return {"rating": 5, "title": "Excellent product!",
                "comment": "Really happy with this purchase.", "productId": "{{product_id}}"}
    if any(x in p for x in ["address", "location", "destination"]):
        return {"label": "Home", "street": "123 Main Street", "city": "Karachi",
                "state": "Sindh", "country": "Pakistan", "zipCode": "75000", "isDefault": True}
    if any(x in p for x in ["coupon", "promo", "voucher", "discount"]):
        return {"code": "SAVE20", "type": "percentage", "value": 20,
                "minOrderAmount": 500, "expiresAt": "2025-12-31"}
    if any(x in p for x in ["category", "categories", "tag"]):
        return {"name": "Electronics", "description": "Electronic devices and gadgets",
                "slug": "electronics", "parentId": None}
    if any(x in p for x in ["notification", "notify", "alert"]):
        return {"title": "New Order", "body": "Your order has been placed",
                "userId": "{{user_id}}", "type": "order"}
    if any(x in p for x in ["upload", "media", "file", "image", "photo", "video", "document"]):
        return "__multipart__"
    if any(x in p for x in ["profile", "me", "myself"]):
        return {"name": "John Doe", "phone": "+923001234567",
                "bio": "Software developer", "avatar": "https://example.com/avatar.jpg"}
    if any(x in p for x in ["user", "account", "member"]):
        return {"name": "John Doe", "phone": "+923001234567",
                "bio": "Software developer", "avatar": "https://example.com/avatar.jpg"}
    return {"key": "value"}


def extract_path_params(path: str) -> list[str]:
    params = re.findall(r':(\w+)', path)
    params += re.findall(r'\{(\w+)\}', path)
    params += re.findall(r'<(?:int:|str:|uuid:|float:)?(\w+)>', path)
    params += re.findall(r'\(\?P<(\w+)>', path)
    return list(dict.fromkeys(params))  # dedupe, preserve order


_AUTH_KEYWORDS = {
    "auth", "login", "logout", "register", "signup", "signin", "refresh",
    "forgot", "reset", "verify", "otp", "2fa", "token", "oauth",
    "password", "credential", "session",
}


def extract_query_params(code_section: str, path: str, method: str = "GET") -> list[str]:
    # Non-GET routes never get pagination
    if method.upper() != "GET":
        return []
    qp: list[str] = []
    qp += re.findall(r'req\.query\.(\w+)', code_section)
    qp += re.findall(r'request\.args\.get\([\"\'](\w+)[\"\']', code_section)
    qp += re.findall(r'request\.GET\.get\([\"\'](\w+)[\"\']', code_section)
    p = path.lower()
    path_parts = [seg for seg in p.split("/") if seg]
    is_auth = any(part in _AUTH_KEYWORDS for part in path_parts)
    if not is_auth:
        is_list = not re.search(r'(:[^/]+|\{[^}]+\}|<[^>]+>)$', path)
        if is_list:
            for param in ['page', 'limit']:
                if param not in qp:
                    qp.append(param)
    if any(x in p for x in ['search', 'find', 'filter', 'query', 'lookup', 'explore', 'discover']):
        if 'q' not in qp:
            qp.append('q')
    return list(dict.fromkeys(qp))


def _normalize_path(path: str) -> str:
    """Convert all param styles to :param for internal use, then normalize slashes."""
    # Django <int:pk> / <str:slug> → :pk / :slug
    path = re.sub(r'<(?:int:|str:|uuid:|float:)?(\w+)>', r':\1', path)
    # Django regex (?P<pk>...) → :pk
    path = re.sub(r'\(\?P<(\w+)>[^)]+\)', r':\1', path)
    # FastAPI/Flask {param} → :param
    path = re.sub(r'\{(\w+)\}', r':\1', path)
    # normalize double slashes
    path = re.sub(r'/+', '/', path)
    return path


def _to_postman_path(path: str) -> str:
    """Convert :param → {{param}} for Postman."""
    return re.sub(r':(\w+)', r'{{\1}}', path)


def extract_routes(code: str) -> list[dict[str, Any]]:
    routes: list[dict] = []
    seen: set[str] = set()
    auth_type = detect_auth_type(code)

    def add_route(method: str, raw_path: str, section_code: str, base: str = ""):
        if not raw_path:
            return
        norm = _normalize_path(raw_path)
        if base:
            if norm == "/":
                full = base.rstrip("/") or "/"
            else:
                full = base.rstrip("/") + "/" + norm.lstrip("/")
        else:
            full = norm
        full = _normalize_path(full)
        if not full.startswith("/"):
            full = "/" + full
        postman_path = _to_postman_path(full)
        key = f"{method.upper()}:{full}"
        if key in seen:
            return
        seen.add(key)
        path_params = extract_path_params(full)
        query_params = extract_query_params(section_code, full, method)
        body = generate_body(full, method.upper())
        # Use base path for folder detection when route path has no useful segments
        folder_path = full if detect_folder(full) not in ("General", "Miscellaneous") else (base or full)
        routes.append({
            "method": method.upper(),
            "path": postman_path,
            "name": generate_name(method.upper(), full),
            "folder": detect_folder(folder_path),
            "path_params": path_params,
            "query_params": query_params,
            "auth_type": auth_type,
            "description": f"{method.upper()} {postman_path}",
            "request_body": body,
        })

    # ── Step 1: Build base-path map from app/server/main files ───────────────
    def build_base_path_map(app_code: str) -> dict[str, str]:
        bmap: dict[str, str] = {}

        # Express: app.use('/api/auth', authRoutes) — matches any variable
        for base, ref in re.findall(
            r'app\.use\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)\s*\)',
            app_code, re.IGNORECASE
        ):
            clean = base.rstrip("/")
            key = ref.lower()
            bmap[key] = clean
            bmap[re.sub(r'[._-]?(routes?|router)$', '', key).strip('._-')] = clean

        # Express: app.use('/api', require('./routes/auth'))
        for base, req_ref in re.findall(
            r'app\.use\s*\(\s*["\']([^"\']+)["\']\s*,\s*require\s*\(["\']([^"\']+)["\']\)',
            app_code, re.IGNORECASE
        ):
            clean = base.rstrip("/")
            stem = re.sub(r'\.(js|ts)$', '', req_ref.split('/')[-1])
            key = stem.lower()
            bmap[key] = clean
            bmap[re.sub(r'[._-]?(routes?|router)$', '', key).strip("._-")] = clean

        # Fastify: fastify.register(plugin, { prefix: '/api/auth' })
        for ref, prefix in re.findall(
            r'(?:fastify|app|server)\.register\s*\(\s*(\w+)\s*,\s*\{[^}]*prefix\s*:\s*["\']([^"\']+)["\']',
            app_code, re.IGNORECASE
        ):
            clean = prefix.rstrip("/")
            key = ref.lower()
            bmap[key] = clean
            bmap[key.replace("routes", "").replace("plugin", "").replace("handler", "").strip("_")] = clean

        # FastAPI: app.include_router(router, prefix='/api/auth')
        for ref, prefix in re.findall(
            r'(?:app|router)\.include_router\s*\(\s*(\w+)\s*,.*?prefix\s*=\s*["\']([^"\']+)["\']',
            app_code, re.IGNORECASE
        ):
            clean = prefix.rstrip("/")
            key = ref.lower()
            bmap[key] = clean
            bmap[key.replace("router", "").replace("_router", "").strip("_")] = clean

        # Flask: app.register_blueprint(bp, url_prefix='/api/auth')
        for ref, prefix in re.findall(
            r'(?:app|factory)\.register_blueprint\s*\(\s*(\w+)\s*,.*?url_prefix\s*=\s*["\']([^"\']+)["\']',
            app_code, re.IGNORECASE
        ):
            clean = prefix.rstrip("/")
            key = ref.lower()
            bmap[key] = clean
            bmap[key.replace("bp", "").replace("blueprint", "").strip("_")] = clean

        return bmap

    def find_base(filename: str, bmap: dict[str, str]) -> str:
        stem = re.sub(r'\.(js|ts|py|mjs|cjs)$', '', filename.lower())
        stem_clean = re.sub(r'[._-]?(routes?|router|controller|handler|views?)$', '', stem).strip("._-")
        for key, base in bmap.items():
            if not key:
                continue
            if key == stem or key == stem_clean or stem.startswith(key) or key.startswith(stem_clean):
                return base
        return ""

    # ── Step 2: Split by FILE_MARKER ─────────────────────────────────────────
    marker_re = re.compile(r'//\s*FILE_MARKER:\s*(\S+)')
    sections_raw = marker_re.split(code)

    if len(sections_raw) > 1:
        # sections_raw = [pre, filename1, content1, filename2, content2, ...]
        # Find app/server/main section first to build base map
        app_filenames = {"app.js", "server.js", "index.js", "main.py", "app.py",
                         "app.ts", "server.ts", "index.ts", "main.ts"}
        app_code_combined = sections_raw[0]  # pre-marker code
        named_sections: list[tuple[str, str]] = []
        i = 1
        while i < len(sections_raw) - 1:
            fname = sections_raw[i].strip()
            content = sections_raw[i + 1]
            named_sections.append((fname, content))
            if fname.lower() in app_filenames:
                app_code_combined += "\n" + content
            i += 2

        bmap = build_base_path_map(app_code_combined)

        for fname, content in named_sections:
            base = find_base(fname, bmap)
            _extract_from_section(content, base, add_route, bmap)
    else:
        # No FILE_MARKER — single blob
        bmap = build_base_path_map(code)
        _extract_from_section(code, "", add_route, bmap)

    print(f"Parser found: {len(routes)} routes")
    return routes


# ── Section-level extraction ──────────────────────────────────────────────────

_JS_ROUTE_RE = re.compile(
    r'(?:router|app|fastify|server|instance|Route)\s*\.'
    r'(get|post|put|delete|patch|head|options)\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE
)

_CHAINED_ROUTE_RE = re.compile(
    r'(?:router|app)\s*\.route\s*\(\s*["\']([^"\']+)["\']\s*\)'
    r'((?:\s*\.\s*(?:get|post|put|delete|patch)\s*\([^)]*\))+)',
    re.IGNORECASE | re.DOTALL
)

_CHAINED_METHOD_RE = re.compile(r'\.\s*(get|post|put|delete|patch)\s*\(', re.IGNORECASE)

_NESTJS_RE = re.compile(
    r'@(Get|Post|Put|Delete|Patch)\s*\(\s*(?:["\']([^"\']*)["\'])?\s*\)',
    re.IGNORECASE
)

_FLASK_ROUTE_RE = re.compile(
    r'@\w+\.route\s*\(\s*["\']([^"\']+)["\'].*?methods\s*=\s*\[([^\]]+)\]',
    re.IGNORECASE | re.DOTALL
)

_FLASK_ROUTE_NO_METHODS_RE = re.compile(
    r'@\w+\.route\s*\(\s*["\']([^"\']+)["\']\s*\)',
    re.IGNORECASE
)

_DJANGO_PATH_RE = re.compile(
    r'(?:path|re_path|url)\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE
)


def _extract_from_section(code: str, base: str, add_route, bmap: dict | None = None):
    """Extract routes from a single code section."""
    found_any = False

    # ── Express / Fastify chained routes ─────────────────────────────────────
    for m in _CHAINED_ROUTE_RE.finditer(code):
        path = m.group(1)
        chain = m.group(2)
        for method_m in _CHAINED_METHOD_RE.finditer(chain):
            add_route(method_m.group(1), path, code, base)
            found_any = True

    # ── Express / Fastify standard routes ────────────────────────────────────
    # Resolve Fastify inline prefix from this section (works in both single & multi-file)
    inline_base = base
    if not inline_base:
        inline = re.search(
            r'\.register\s*\([^,]+,\s*\{[^}]*prefix\s*:\s*["\']([^"\']+)["\']',
            code, re.IGNORECASE
        )
        if inline:
            inline_base = inline.group(1).rstrip("/")
        elif bmap is not None:
            # Only match bmap key if it's defined (exported/declared) in this section
            for key, mapped_base in bmap.items():
                if key and re.search(rf'(?:const|let|var|export)\s+{re.escape(key)}\b', code, re.IGNORECASE):
                    inline_base = mapped_base
                    break
    for m in _JS_ROUTE_RE.finditer(code):
        method, path = m.group(1), m.group(2)
        add_route(method, path, code, inline_base)
        found_any = True

    # ── NestJS decorators ─────────────────────────────────────────────────────
    for m in _NESTJS_RE.finditer(code):
        method = m.group(1)
        path = m.group(2) or ""
        if not path.startswith("/"):
            path = "/" + path
        add_route(method, path, code, base)
        found_any = True

    # ── Flask routes ──────────────────────────────────────────────────────────
    flask_found = False
    for m in _FLASK_ROUTE_RE.finditer(code):
        path = m.group(1)
        methods = [x.strip().strip("\"'") for x in m.group(2).split(",")]
        for method in methods:
            if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"):
                add_route(method, path, code, base)
                flask_found = found_any = True

    # Flask routes without explicit methods (default GET)
    if not flask_found:
        for m in _FLASK_ROUTE_NO_METHODS_RE.finditer(code):
            add_route("GET", m.group(1), code, base)
            found_any = True

    # ── FastAPI / generic Python decorators ──────────────────────────────────
    if not flask_found:
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                            method = dec.func.attr.lower()
                            if method in ("get", "post", "put", "delete", "patch"):
                                if dec.args and isinstance(dec.args[0], ast.Constant):
                                    add_route(method, str(dec.args[0].value), code, base)
                                    found_any = True
        except SyntaxError:
            pass

    # ── Django url patterns ───────────────────────────────────────────────────
    if not found_any:
        # Try to infer HTTP method from view class name
        view_method_map: dict[str, str] = {}
        for vcls, vmeth in re.findall(
            r'class\s+(\w+)\s*\([^)]*\).*?def\s+(get|post|put|delete|patch)\s*\(self',
            code, re.IGNORECASE | re.DOTALL
        ):
            view_method_map[vcls.lower()] = vmeth.upper()

        for m in _DJANGO_PATH_RE.finditer(code):
            raw = m.group(1)
            if "." in raw and "/" not in raw:
                continue
            path = raw if raw.startswith("/") else "/" + raw
            # Look ahead for view reference to guess method
            context = code[m.start():m.start() + 200]
            method = "GET"
            for vcls, vmeth in view_method_map.items():
                if vcls in context.lower():
                    method = vmeth
                    break
            add_route(method, path, code, base)
