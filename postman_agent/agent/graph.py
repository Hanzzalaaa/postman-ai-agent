import json
import os
import re
import uuid
from typing import Annotated

import httpx
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from pydantic import SecretStr
from typing_extensions import TypedDict

from postman_agent.tools.code_parser import extract_routes

load_dotenv()


# ── Provider / Model Registry ──────────────────────────────────────────────────────
PROVIDER_MODELS: dict[str, list[str]] = {
    "groq": [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "gemma-7b-it",
    ],
    "gemini": [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash-preview",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
    ],
    "glm": [
        "glm-4-flash",
        "glm-4v-flash",
        "glm-4-flashx",
        "glm-4-air",
        "glm-4-airx",
        "glm-zero-preview",
    ],
    "ollama": [
        "llama3.2",
        "llama3.1",
        "mistral",
        "codellama",
        "qwen2.5",
        "phi3",
        "gemma2",
        "deepseek-r1",
        "deepseek-coder",
    ],
    "cerebras": [
        "llama3.1-8b",
        "llama3.1-70b",
        "llama-4-scout-17b-16e-instruct",
    ],
    "sambanova": [
        "Meta-Llama-3.1-8B-Instruct",
        "Meta-Llama-3.1-70B-Instruct",
        "Meta-Llama-3.1-405B-Instruct",
    ],
    "cloudflare": [
        "@cf/meta/llama-3.1-8b-instruct",
        "@cf/mistral/mistral-7b-instruct-v0.1",
        "@cf/qwen/qwen1.5-14b-chat-awq",
    ],
    "together": [
        "meta-llama/Llama-3.2-3B-Instruct-Turbo",
        "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
    ],
    "fireworks": [
        "accounts/fireworks/models/llama-v3p1-8b-instruct",
        "accounts/fireworks/models/llama-v3p2-3b-instruct",
    ],
    "huggingface": [
        "meta-llama/Llama-3.2-3B-Instruct",
        "microsoft/Phi-3.5-mini-instruct",
    ],
    "openrouter": [
        "google/gemma-2-9b-it:free",
        "mistralai/mistral-7b-instruct:free",
        "meta-llama/llama-3.2-3b:free",
        "microsoft/phi-3-mini-128k:free",
        "huggingfaceh4/zephyr-7b-beta:free",
    ],
    "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    "anthropic": [
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
    ],
    "mistral": ["mistral-small-latest", "mistral-large-latest", "open-mixtral-8x7b"],
    "cohere": ["command-r-plus", "command-r", "command"],
}


# ── LLM Factory ───────────────────────────────────────────────────────────────────
def get_llm(provider: str | None = None, model: str | None = None):
    """Dynamic LLM factory — supports all free and paid providers."""
    provider = (provider or os.getenv("LLM_PROVIDER", "groq")).lower()
    model = model or os.getenv("LLM_MODEL") or PROVIDER_MODELS[provider][0] if provider in PROVIDER_MODELS else None

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(api_key=SecretStr(os.getenv("GROQ_API_KEY") or ""), model=model, temperature=0)

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(google_api_key=os.getenv("GOOGLE_API_KEY"), model=model, temperature=0)

    elif provider == "glm":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(api_key=SecretStr(os.getenv("ZHIPU_API_KEY") or ""), model=model, base_url="https://open.bigmodel.cn/api/paas/v4/", temperature=0)

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=0)

    elif provider == "cerebras":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(api_key=SecretStr(os.getenv("CEREBRAS_API_KEY") or ""), model=model, base_url="https://api.cerebras.ai/v1/", temperature=0)

    elif provider == "sambanova":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(api_key=SecretStr(os.getenv("SAMBANOVA_API_KEY") or ""), model=model, base_url="https://fast-api.snova.ai/v1/", temperature=0)

    elif provider == "cloudflare":
        from langchain_openai import ChatOpenAI
        account_id = os.getenv("CF_ACCOUNT_ID", "")
        return ChatOpenAI(api_key=SecretStr(os.getenv("CF_API_TOKEN") or ""), model=model, base_url=f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/", temperature=0)

    elif provider == "together":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(api_key=SecretStr(os.getenv("TOGETHER_API_KEY") or ""), model=model, base_url="https://api.together.xyz/v1/", temperature=0)

    elif provider == "fireworks":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(api_key=SecretStr(os.getenv("FIREWORKS_API_KEY") or ""), model=model, base_url="https://api.fireworks.ai/inference/v1/", temperature=0)

    elif provider == "huggingface":
        from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
        endpoint = HuggingFaceEndpoint(repo_id=model, huggingfacehub_api_token=os.getenv("HF_API_KEY"), temperature=0)
        return ChatHuggingFace(llm=endpoint)

    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(api_key=SecretStr(os.getenv("OPENROUTER_API_KEY") or ""), model=model, base_url="https://openrouter.ai/api/v1/", temperature=0)

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(api_key=SecretStr(os.getenv("OPENAI_API_KEY") or ""), model=model, temperature=0)

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(api_key=SecretStr(os.getenv("ANTHROPIC_API_KEY") or ""), model=model, temperature=0)

    elif provider == "mistral":
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(api_key=SecretStr(os.getenv("MISTRAL_API_KEY") or ""), model=model, temperature=0)

    elif provider == "cohere":
        from langchain_cohere import ChatCohere
        return ChatCohere(cohere_api_key=os.getenv("COHERE_API_KEY"), model=model, temperature=0)

    else:
        raise ValueError(
            f"Unknown provider: '{provider}'\n"
            f"Available: {', '.join(PROVIDER_MODELS.keys())}"
        )


# ── State ─────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    code: str
    routes: list
    postman_collection: dict
    postman_import: dict
    project_name: str
    base_url: str
    token: str
    force_ai: bool
    provider: str
    model: str


# ── Postman Import ────────────────────────────────────────────────────────────
def _get_headers() -> dict:
    return {"X-Api-Key": os.getenv("POSTMAN_API_KEY", ""), "Content-Type": "application/json"}


def _find_existing_collection(name: str, headers: dict) -> str | None:
    """Return UID of existing collection with same name, or None."""
    try:
        resp = httpx.get("https://api.getpostman.com/collections", headers=headers, timeout=15)
        if resp.status_code == 200:
            for col in resp.json().get("collections", []):
                if col.get("name") == name:
                    return col.get("uid")
    except Exception:
        pass
    return None


def import_to_postman(collection: dict) -> dict:
    """Create or update a Postman Collection — no duplicates."""
    api_key = os.getenv("POSTMAN_API_KEY")
    if not api_key:
        return {"success": False, "error": "POSTMAN_API_KEY not set. Run: postman-agent setup"}

    headers = _get_headers()
    name = collection.get("info", {}).get("name", "")
    collection.get("info", {}).pop("_postman_id", None)

    existing_uid = _find_existing_collection(name, headers)

    try:
        if existing_uid:
            response = httpx.put(
                f"https://api.getpostman.com/collections/{existing_uid}",
                headers=headers,
                json={"collection": collection},
                timeout=30,
            )
            action = "updated"
        else:
            response = httpx.post(
                "https://api.getpostman.com/collections",
                headers=headers,
                json={"collection": collection},
                timeout=30,
            )
            action = "created"

        if response.status_code in (200, 201):
            data = response.json().get("collection", {})
            uid = existing_uid or data.get("uid", "")
            return {
                "success": True,
                "action": action,
                "message": f"Collection '{name}' {action} successfully!",
                "collection_id": uid,
                "postman_url": f"https://go.postman.co/collection/{uid}",
            }
        return {"success": False, "error": f"Postman API {response.status_code}: {response.text}"}
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Folder ordering ──────────────────────────────────────────────────────────
_FOLDER_ORDER = [
    "Authentication", "Users", "Profile", "Products", "Orders", "Payments",
    "Cart", "Wishlist", "Categories", "Reviews", "Addresses", "Coupons",
    "Uploads", "Shipping", "Notifications", "Admin", "Search", "Reports", "Health",
]


def _path_to_postman(path: str) -> tuple[list[str], list[dict], str]:
    """Convert route path (already in {{param}} form) to Postman parts, variables, raw URL."""
    parts = []
    variables = []
    for segment in path.split("/"):
        if not segment:
            continue
        m = re.match(r'^\{\{(\w+)\}\}$', segment)
        if m:
            var_name = m.group(1)
            parts.append(f"{{{{{var_name}}}}}")  # keep {{param}} in path array
            variables.append({"key": var_name, "value": f"{{{{{var_name}}}}}", "description": ""})
        else:
            parts.append(segment)
    raw = "{{base_url}}/" + "/".join(parts)
    return parts, variables, raw


def build_postman_collection(
    routes: list,
    project_name: str = "API Collection",
    base_url: str = "http://localhost:3000",
    token: str = "your_jwt_token_here",
) -> dict:
    """Build a Postman Collection v2.1 from a list of route dicts."""
    from postman_agent.tools.code_parser import detect_folder

    # Re-assign General folder routes
    for route in routes:
        if not route.get("folder") or route["folder"] == "General":
            route["folder"] = detect_folder(route.get("path", "")) or "Miscellaneous"
            if route["folder"] == "General":
                route["folder"] = "Miscellaneous"

    groups: dict[str, list] = {}
    for route in routes:
        groups.setdefault(route["folder"], []).append(route)

    # Sort folders by defined order, then alphabetically
    def folder_sort_key(name: str) -> tuple:
        try:
            return (0, _FOLDER_ORDER.index(name))
        except ValueError:
            return (1, name.lower())

    items = []
    all_path_params: set[str] = set()

    for group_name in sorted(groups.keys(), key=folder_sort_key):
        group_routes = groups[group_name]
        group_items = []
        for route in group_routes:
            method = route.get("method", "GET")
            path = route.get("path", "/")
            path_parts, path_variables, raw_url = _path_to_postman(path)

            for pv in path_variables:
                all_path_params.add(pv["key"])

            query_params = [
                {"key": q, "value": "1" if q in ("page", "limit") else "",
                 "description": "Page number" if q == "page" else "Items per page" if q == "limit" else ""}
                for q in route.get("query_params", [])
            ]
            if query_params:
                raw_url += "?" + "&".join(f"{q['key']}={q['value']}" for q in query_params)

            url_obj: dict = {
                "raw": raw_url,
                "host": ["{{base_url}}"],
                "path": path_parts,
            }
            if path_variables:
                url_obj["variable"] = path_variables
            if query_params:
                url_obj["query"] = query_params

            item: dict = {
                "name": route.get("name", path),
                "request": {
                    "method": method,
                    "description": route.get("description", ""),
                    "header": [
                        {"key": "Authorization", "value": "Bearer {{token}}"},
                    ],
                    "url": url_obj,
                },
            }

            if method in ("POST", "PUT", "PATCH"):
                body = route.get("ai_body") or route.get("request_body")
                if body == "__multipart__":
                    item["request"]["body"] = {
                        "mode": "formdata",
                        "formdata": [
                            {"key": "file", "type": "file", "src": ""},
                            {"key": "type", "value": "image", "type": "text"},
                        ],
                    }
                elif body:
                    item["request"]["header"].append(
                        {"key": "Content-Type", "value": "application/json"}
                    )
                    item["request"]["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(body, indent=2),
                        "options": {"raw": {"language": "json"}},
                    }

            group_items.append(item)
        items.append({"name": group_name, "item": group_items})

    variables = [
        {"key": "base_url", "value": base_url},
        {"key": "token", "value": token},
        {"key": "refresh_token", "value": ""},
    ]
    for param in sorted(all_path_params):
        if param not in ("id",):
            variables.append({"key": param, "value": ""})

    return {
        "info": {
            "name": project_name,
            "_postman_id": str(uuid.uuid4()),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": "Auto-generated by Postman AI Agent",
        },
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{token}}", "type": "string"}],
        },
        "item": items,
        "variable": variables,
    }


# ── LLM helper ────────────────────────────────────────────────────────────────
def _get_llm(provider: str | None = None, model: str | None = None):
    """Return an LLM instance, or None on failure."""
    try:
        return get_llm(provider, model)
    except Exception:
        return None


def _parse_llm_json(raw: str) -> list | None:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'```\s*$', '', raw)
    try:
        result = json.loads(raw.strip())
        return result if isinstance(result, list) else None
    except Exception:
        return None


_SYSTEM_PROMPT = """You are an expert API analyzer and Postman Collection specialist.

You will receive:
1. Original backend code
2. Routes already extracted by a regex parser

Your job (in order):
1. VERIFY: Check if parser missed any routes in the code
2. FIX: Correct any wrong folder names, route names, or paths
3. ENHANCE: Improve descriptions and request bodies

Rules:
- Folders must be: Authentication, Users, Profile, Products, Orders, Payments,
  Cart, Wishlist, Categories, Reviews, Addresses, Coupons, Uploads, Shipping,
  Notifications, Admin, Health, Search, Reports, or a logical custom name
- NEVER use "General" as folder name — always find the right category
- Route names must be human-readable: "Login User", "Get All Products"
- Return ONLY a valid JSON array, no explanation, no markdown

Output format:
[
  {
    "method": "POST",
    "path": "/api/auth/login",
    "name": "Login User",
    "folder": "Authentication",
    "description": "Authenticate user and return JWT token",
    "path_params": [],
    "query_params": [],
    "auth_type": "JWT",
    "request_body": {"email": "john@example.com", "password": "SecurePass123!"}
  }
]"""


def _ai_enhance_routes(routes: list, code: str, provider: str | None = None, model: str | None = None) -> list:
    """Enhance routes via LLM in parallel batches of 25."""
    llm = _get_llm(provider, model)
    if not llm:
        return routes

    def _process_batch(batch: list) -> list:
        user_prompt = f"""Backend Code (excerpt):
{code[:1500]}

Routes:
{json.dumps(batch, indent=2)}

Fix folder names, route names, add descriptions and request bodies.
Return ONLY JSON array."""
        try:
            response = llm.invoke(
                [
                    SystemMessage(content=_SYSTEM_PROMPT),
                    HumanMessage(content=user_prompt),
                ],
                config={"timeout": 60},
            )
            return _parse_llm_json(response.content) or batch
        except Exception:
            return batch

    import concurrent.futures
    BATCH_SIZE = 25
    batches = [routes[i:i + BATCH_SIZE] for i in range(0, len(routes), BATCH_SIZE)]

    llm_results: list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(3, len(batches))) as executor:
        futures = [executor.submit(_process_batch, b) for b in batches]
        for f in concurrent.futures.as_completed(futures):
            llm_results.extend(f.result())

    # Deduplicate: LLM result primary, parser routes as safety net
    seen: set[str] = set()
    merged: list = []
    for r in llm_results:
        key = f"{r.get('method','GET').upper()}:{r.get('path','')}"
        if key not in seen:
            seen.add(key)
            merged.append(r)
    for r in routes:
        key = f"{r.get('method','GET').upper()}:{r.get('path','')}"
        if key not in seen:
            seen.add(key)
            merged.append(r)
    return merged


# ── Graph Nodes ───────────────────────────────────────────────────────────────
def _deduplicate(routes: list) -> list:
    seen = set()
    unique = []
    for route in routes:
        key = f"{route.get('method', 'GET').upper()}:{route.get('path', '')}"
        if key not in seen:
            seen.add(key)
            unique.append(route)
    return unique


def agent_node(state: AgentState) -> AgentState:
    routes = _deduplicate(extract_routes(state["code"]))
    return {
        **state,
        "messages": [HumanMessage(content=f"Extracted {len(routes)} routes")],
        "routes": routes,
    }


def ai_enhance_node(state: AgentState) -> AgentState:
    routes = state["routes"]
    provider = state.get("provider") or None
    model = state.get("model") or None
    print(f"Enhancing {len(routes)} routes with AI ({provider or os.getenv('LLM_PROVIDER', 'groq')})...")
    enhanced = _ai_enhance_routes(routes, state["code"], provider, model)
    return {
        **state,
        "messages": [HumanMessage(content=f"Routes enhanced by AI ({len(enhanced)} total)")],
        "routes": enhanced,
    }


def generate_node(state: AgentState) -> AgentState:
    routes = state["routes"]
    # Log orphan routes before building collection
    orphans = [r for r in routes if not r.get("folder") or r["folder"] in ("General", "Miscellaneous")]
    if orphans:
        print(f"⚠️  {len(orphans)} orphan route(s) re-assigned:")
        for r in orphans:
            print(f"   {r['method']} {r['path']} → folder will be re-detected")
    collection = build_postman_collection(
        routes,
        state.get("project_name", "API Collection"),
        state.get("base_url", "http://localhost:3000"),
        state.get("token", "your_jwt_token_here"),
    )
    import_result = import_to_postman(collection)
    return {
        **state,
        "messages": [HumanMessage(content="Collection generated and imported")],
        "postman_collection": collection,
        "postman_import": import_result,
    }


# ── Graph ─────────────────────────────────────────────────────────────────────
def _build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("ai_enhance", ai_enhance_node)
    graph.add_node("generate", generate_node)
    graph.set_entry_point("agent")
    graph.add_edge("agent", "ai_enhance")
    graph.add_edge("ai_enhance", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


agent = _build_graph()
