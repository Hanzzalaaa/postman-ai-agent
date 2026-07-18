import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.text import Text
from rich.align import Align
from rich.rule import Rule
import rich.box as box
# Windows terminal safe console — force UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
console = Console(highlight=False, force_terminal=True)


# ─── Provider Registry ────────────────────────────────────────────────────────
# (provider_id, display_name, env_key, default_model, is_free)
FREE_PROVIDERS: dict[str, tuple] = {
    "1":  ("groq",        "Groq",              "GROQ_API_KEY",       "llama-3.1-8b-instant",                            True),
    "2":  ("gemini",      "Google Gemini",      "GOOGLE_API_KEY",     "gemini-2.0-flash",                                True),
    "3":  ("glm",         "GLM / Zhipu AI",     "ZHIPU_API_KEY",      "glm-4-flash",                                     True),
    "4":  ("ollama",      "Ollama (Local)",      None,                 "llama3.2",                                        True),
    "5":  ("cerebras",    "Cerebras",            "CEREBRAS_API_KEY",   "llama3.1-8b",                                     True),
    "6":  ("sambanova",   "SambaNova",           "SAMBANOVA_API_KEY",  "Meta-Llama-3.1-8B-Instruct",                      True),
    "7":  ("cloudflare",  "Cloudflare AI",       "CF_API_TOKEN",       "@cf/meta/llama-3.1-8b-instruct",                  True),
    "8":  ("together",    "Together AI",         "TOGETHER_API_KEY",   "meta-llama/Llama-3.2-3B-Instruct-Turbo",          True),
    "9":  ("fireworks",   "Fireworks AI",        "FIREWORKS_API_KEY",  "accounts/fireworks/models/llama-v3p1-8b-instruct", True),
    "10": ("huggingface", "Hugging Face",        "HF_API_KEY",         "meta-llama/Llama-3.2-3B-Instruct",                True),
    "11": ("openrouter",  "OpenRouter (Free)",   "OPENROUTER_API_KEY", "google/gemma-2-9b-it:free",                       True),
    "12": ("openai",      "OpenAI",              "OPENAI_API_KEY",     "gpt-4o-mini",                                     False),
    "13": ("anthropic",   "Anthropic Claude",    "ANTHROPIC_API_KEY",  "claude-3-haiku-20240307",                         False),
    "14": ("mistral",     "Mistral",             "MISTRAL_API_KEY",    "mistral-small-latest",                            False),
    "15": ("cohere",      "Cohere",              "COHERE_API_KEY",     "command-r-plus",                                  False),
}


def _load_env() -> None:
    for path in (
        Path.home() / ".postman-agent" / ".env",
        Path.cwd() / ".env",
    ):
        if path.exists():
            load_dotenv(path, override=True)


def _print_banner() -> None:
    lines = [
        ("POSTMAN", "#6C63FF"),
        ("AI AGENT", "#8A85FF"),
    ]
    for line, color in lines:
        console.print(Text(line, style=f"bold {color}", justify="center"))
        time.sleep(0.05)

    subtitle = Text(justify="center")
    subtitle.append("  * ", style="bold #6C63FF")
    subtitle.append("AI Agent", style="bold #F0F0FF")
    subtitle.append("  |  ", style="dim #6C63FF")
    subtitle.append("LangGraph", style="#10B981")
    subtitle.append(" x ", style="dim #F0F0FF")
    subtitle.append("Multi-Provider LLM", style="#10B981")
    subtitle.append("  * ", style="bold #6C63FF")

    console.print()
    console.print(Panel(
        Align.center(subtitle),
        border_style="#6C63FF",
        padding=(0, 4),
    ))
    console.print()

def _detect_framework(code: str) -> str:
    code_lower = code.lower()
    if "fastify" in code_lower:
        return "Fastify"
    if "express" in code_lower or "router." in code_lower:
        return "Express.js"
    if "fastapi" in code_lower:
        return "FastAPI"
    if "flask" in code_lower:
        return "Flask"
    if "django" in code_lower or "urlpatterns" in code_lower:
        return "Django"
    return "Unknown"


_API_PATTERNS = [
    r'(?:router|app|fastify)\.(get|post|put|delete|patch)\s*\(',
    r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(',
    r'@\w+\.route\s*\(',
    r'(?:path|re_path|url)\s*\(\s*["\']',
    r'app\.use\s*\(\s*["\']/',
]


def _is_api_file(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        return any(re.search(p, content, re.IGNORECASE) for p in _API_PATTERNS)
    except Exception:
        return False


_EXCLUDED_DIRS = {
    "node_modules", "venv", ".venv", "env", "__pycache__",
    ".git", "dist", "build", "out", ".next", "coverage", "vendor",
}


async def _run_agent(
    code: str,
    project_name: str = "API Collection",
    base_url: str = "http://localhost:3000",
    token: str = "your_jwt_token_here",
    force_ai: bool = False,
    provider: str = "",
    model: str = "",
) -> dict:
    from postman_agent.agent.graph import agent, AgentState
    state: AgentState = {
        "messages": [],
        "code": code,
        "routes": [],
        "postman_collection": {},
        "postman_import": {},
        "project_name": project_name,
        "base_url": base_url,
        "token": token,
        "force_ai": force_ai,
        "provider": provider,
        "model": model,
    }
    return await agent.ainvoke(state)


# ─── setup command ────────────────────────────────────────────────────────────
def setup_command(_args: argparse.Namespace) -> None:
    _print_banner()
    console.print("[bold #6C63FF]  LLM Provider Setup[/]\n")

    # Show numbered list of providers
    console.print("  [dim]FREE PROVIDERS:[/]")
    for k, v in FREE_PROVIDERS.items():
        if v[4]:
            console.print(f"  {k}) {v[1]}")
    console.print("  [dim]PAID PROVIDERS:[/]")
    for k, v in FREE_PROVIDERS.items():
        if not v[4]:
            console.print(f"  {k}) {v[1]} [paid]")

    choice_key = input("\n  Enter number (default 1): ").strip() or "1"
    if choice_key not in FREE_PROVIDERS:
        console.print("[red]Invalid choice.[/]")
        return

    provider_id, display_name, env_key, default_model, is_free = FREE_PROVIDERS[choice_key]
    tier = "FREE" if is_free else "PAID"
    console.print(f"\n  Selected: {display_name} ({tier})\n")

    env_lines = [f"LLM_PROVIDER={provider_id}\n"]

    if env_key:
        api_key = input(f"  {env_key}: ").strip()
        if api_key:
            masked = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****"
            console.print(f"  Key saved: {masked}")
            env_lines.append(f"{env_key}={api_key}\n")
        if provider_id == "cloudflare":
            account_id = input("  Cloudflare Account ID: ").strip()
            if account_id:
                env_lines.append(f"CF_ACCOUNT_ID={account_id}\n")
    else:
        console.print(f"  {display_name} runs locally - no API key needed")

    model_input = input(f"  Model (Enter for default '{default_model}'): ").strip()
    chosen_model = model_input if model_input else default_model
    env_lines.append(f"LLM_MODEL={chosen_model}\n")

    console.print("\n  Postman API Key")
    postman_key = input("  POSTMAN_API_KEY: ").strip()
    if postman_key:
        masked_pm = postman_key[:4] + "*" * max(0, len(postman_key) - 8) + postman_key[-4:] if len(postman_key) > 8 else "****"
        console.print(f"  Key saved: {masked_pm}")
        env_lines.append(f"POSTMAN_API_KEY={postman_key}\n")

    env_dir = Path.home() / ".postman-agent"
    env_dir.mkdir(exist_ok=True)
    env_file = env_dir / ".env"

    existing: dict[str, str] = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()

    new_keys = {line.partition("=")[0].strip() for line in env_lines if "=" in line}
    for k, v in existing.items():
        if k not in new_keys:
            env_lines.append(f"{k}={v}\n")

    env_file.write_text("".join(env_lines))
    
    console.print()
    config_table = Table(show_header=False, box=None, padding=(0, 2))
    config_table.add_row("[dim]File[/]",     f"[#F0F0FF]{env_file}[/]")
    config_table.add_row("[dim]Provider[/]", f"[bold #6C63FF]{display_name}[/]")
    config_table.add_row("[dim]Model[/]",    f"[#10B981]{chosen_model}[/]")
    console.print(Panel(config_table, title="[bold #6C63FF]◆ Configuration Saved[/]", border_style="#6C63FF", padding=(0, 1)))
    console.print(f"\n  [bold #10B981]Ready![/] Run: [bold #6C63FF]postman-agent generate --scan .[/]\n")


# ─── providers command ────────────────────────────────────────────────────────
def providers_command(_args: argparse.Namespace) -> None:
    from postman_agent.agent.graph import PROVIDER_MODELS
    _load_env()
    current = os.getenv("LLM_PROVIDER", "groq")

    console.print("\n[bold cyan]FREE PROVIDERS[/]\n")
    free_table = Table(show_header=True, box=None)
    free_table.add_column("Provider", style="cyan")
    free_table.add_column("Default Model", style="green")
    free_table.add_column("Status", style="dim")
    
    for num, (pid, name, env_key, default_model, is_free) in FREE_PROVIDERS.items():
        if not is_free:
            continue
        active = "[green]* active[/]" if pid == current else ""
        free_table.add_row(pid, default_model, active)
    console.print(free_table)

    console.print("\n[bold cyan]PAID PROVIDERS[/]\n")
    paid_table = Table(show_header=True, box=None)
    paid_table.add_column("Provider", style="cyan")
    paid_table.add_column("Default Model", style="yellow")
    paid_table.add_column("Status", style="dim")
    
    for num, (pid, name, env_key, default_model, is_free) in FREE_PROVIDERS.items():
        if is_free:
            continue
        active = "[green]* active[/]" if pid == current else ""
        paid_table.add_row(pid, default_model, active)
    console.print(paid_table)
    console.print()


# ─── models command ───────────────────────────────────────────────────────────
def models_command(args: argparse.Namespace) -> None:
    from postman_agent.agent.graph import PROVIDER_MODELS
    provider = args.provider.lower()
    if provider not in PROVIDER_MODELS:
        console.print(f"[red]✗[/] Unknown provider '{provider}'. Run: [bold cyan]postman-agent providers[/]")
        sys.exit(1)
    
    console.print(f"\n[bold cyan]Models for '{provider}'[/]\n")
    models_table = Table(show_header=False, box=None)
    for i, m in enumerate(PROVIDER_MODELS[provider]):
        default_note = "[dim](default)[/]" if i == 0 else ""
        models_table.add_row(m, default_note)
    console.print(models_table)
    console.print()


# ─── Folder → emoji mapping ───────────────────────────────────────────────────
_FOLDER_ICONS: dict[str, str] = {
    "auth":     "🔐", "authentication": "🔐", "login":   "🔐", "register": "🔐",
    "user":     "👤", "users":          "👤", "profile": "👤", "account":  "👤",
    "product":  "📦", "products":        "📦", "item":    "📦", "items":    "📦",
    "order":    "🛒", "orders":          "🛒", "cart":    "🛒", "checkout": "🛒",
    "payment":  "💳", "payments":        "💳", "billing": "💳", "invoice":  "💳",
    "admin":    "⚙️",  "dashboard":       "📊", "report":  "📊", "analytics":"📊",
    "file":     "📁", "upload":          "📁", "media":   "🖼️",
    "message":  "💬", "chat":            "💬", "notification": "🔔",
    "search":   "🔍", "health":          "💚", "webhook": "🔗",
}

def _folder_icon(name: str) -> str:
    key = name.lower().strip()
    for k, icon in _FOLDER_ICONS.items():
        if k in key:
            return icon
    return "📂"


def _scan_code(args: argparse.Namespace) -> tuple[str, str, list[Path]]:
    """Scan file or directory and return (code, project_name, api_files)."""
    project_name = "API Collection"

    if args.file:
        raw_path = Path(args.file).resolve()
        if not raw_path.exists() or not raw_path.is_file():
            console.print(f"  [red]✗[/] File not found: {args.file}")
            sys.exit(1)
        if raw_path.suffix not in (".js", ".ts", ".py"):
            console.print(f"  [red]✗[/] Unsupported file type: {raw_path.suffix}")
            sys.exit(1)
        code = raw_path.read_text(encoding="utf-8", errors="ignore")
        project_name = raw_path.stem.replace("-", " ").replace("_", " ").title()
        return code, project_name, [raw_path]

    elif args.scan:
        scan_path = Path(args.scan).resolve()
        if not scan_path.exists() or not scan_path.is_dir():
            console.print(f"  [red]✗[/] Directory not found: {args.scan}")
            sys.exit(1)
        all_files = [
            f
            for ext in (".js", ".ts", ".py")
            for f in scan_path.rglob(f"*{ext}")
            if not any(ex in f.parts for ex in _EXCLUDED_DIRS)
        ]
        api_files = [f for f in all_files if _is_api_file(f)]
        if not api_files:
            console.print("  [red]✗[/] No API files found.")
            sys.exit(1)
        code = "\n".join(
            f"// FILE_MARKER: {f.name}\n{f.read_text(encoding='utf-8', errors='ignore')}"
            for f in api_files
        )
        project_name = scan_path.name.replace("-", " ").replace("_", " ").title()
        if args.name:
            project_name = args.name
        return code, project_name, api_files

    console.print("  [red]✗[/] Provide --file or --scan")
    sys.exit(1)


def _print_result(
    routes: list,
    postman_collection: dict,
    postman_import: dict,
    args: argparse.Namespace,
    elapsed: float = 0.0,
) -> None:
    # ── Group routes by folder ────────────────────────────────────────────────
    folders: dict[str, list] = {}
    for r in routes:
        folder = r.get("folder") or r.get("group") or "General"
        folders.setdefault(folder, []).append(r)

    if folders:
        console.print()
        console.print(Rule("[bold #6C63FF]  Route Groups  ", style="#6C63FF"))
        console.print()

        rows: list[tuple] = []
        for fname in sorted(folders, key=lambda n: (0 if "auth" in n.lower() else 1, n)):
            icon    = _folder_icon(fname)
            count   = len(folders[fname])
            methods = ", ".join(sorted({r.get("method", "GET") for r in folders[fname]}))
            rows.append((f"{icon}  {fname}", str(count), methods))

        from rich.live import Live
        tbl = Table(
            show_header=True,
            header_style="bold #6C63FF",
            border_style="#6C63FF",
            box=box.ROUNDED,
            padding=(0, 1),
        )
        tbl.add_column("Folder",  style="#F0F0FF", min_width=22)
        tbl.add_column("Routes",  style="bold #10B981", justify="right", min_width=7)
        tbl.add_column("Methods", style="dim #F0F0FF", min_width=28)

        with Live(tbl, console=console, refresh_per_second=12):
            for fname_cell, count_cell, methods_cell in rows:
                tbl.add_row(fname_cell, count_cell, methods_cell)
                time.sleep(0.10)

    console.print()

    # ── dry-run / output ──────────────────────────────────────────────────────
    if getattr(args, "dry_run", False):
        console.print("  [yellow]⚠[/]  Dry run — skipping Postman import.")
        if args.output:
            out = Path(args.output).resolve()
            out.write_text(json.dumps(postman_collection, indent=2), encoding="utf-8")
            console.print(f"  [#10B981]✓[/]  Saved → [bold #6C63FF]{out}[/]")
        return

    if args.output:
        out = Path(args.output).resolve()
        out.write_text(json.dumps(postman_collection, indent=2), encoding="utf-8")
        console.print(f"  [#10B981]✓[/]  Saved → [bold #6C63FF]{out}[/]")

    # ── success / failure panel ───────────────────────────────────────────────
    if postman_import.get("success"):
        coll_name = postman_collection.get("info", {}).get("name", "API Collection")
        url       = postman_import.get("postman_url", "")
        action    = postman_import.get("action", "imported")
        elapsed_s = f"{elapsed:.1f}s"

        success_text = Text()
        success_text.append(f"  OK  Collection {action}\n\n", style="bold #10B981")
        success_text.append("  Name   ", style="dim")
        success_text.append(f"{coll_name}\n", style="bold #F0F0FF")
        success_text.append("  Routes ", style="dim")
        success_text.append(f"{len(routes)}\n", style="bold #10B981")
        success_text.append("  Time   ", style="dim")
        success_text.append(f"{elapsed_s}\n", style="#F0F0FF")
        success_text.append("  URL    ", style="dim")
        success_text.append(url, style="bold #6C63FF")

        console.print(Panel(
            success_text,
            border_style="#10B981",
            padding=(0, 2),
            title="[bold #10B981]◆ Done[/]",
        ))
    else:
        err = postman_import.get("error", "Unknown error")
        console.print(Panel(
            f"  [red]✗[/]  Import failed: {err}\n\n  Run: [bold #6C63FF]postman-agent setup[/]",
            border_style="red",
            padding=(0, 2),
        ))


def _check_provider_key(provider: str) -> None:
    """Warn if the required env key for the chosen provider is missing."""
    for _, (pid, name, env_key, _, _) in FREE_PROVIDERS.items():
        if pid == provider:
            if env_key and not os.getenv(env_key):
                print(f"ERROR: {env_key} not set for provider '{provider}'. Run: postman-agent setup")
                sys.exit(1)
            return


def generate_command(args: argparse.Namespace) -> None:
    _print_banner()
    _load_env()

    provider = getattr(args, "provider", None) or os.getenv("LLM_PROVIDER", "groq")
    model    = getattr(args, "model",    None) or os.getenv("LLM_MODEL", "")

    _check_provider_key(provider)

    if not getattr(args, "dry_run", False) and not os.getenv("POSTMAN_API_KEY"):
        console.print("  [red]✗[/]  POSTMAN_API_KEY not found. Run: [bold #6C63FF]postman-agent setup[/]")
        sys.exit(1)

    # ── Phase 1: Scan ─────────────────────────────────────────────────────────
    console.print(Rule("[bold #6C63FF]  Scanning  ", style="#6C63FF"))
    console.print()

    code, project_name, api_files = _scan_code(args)
    framework = _detect_framework(code)

    scan_table = Table(show_header=False, box=None, padding=(0, 1))
    scan_table.add_column(style="dim")
    scan_table.add_column(style="#F0F0FF")
    scan_table.add_row("  Project",   f"[bold #6C63FF]{project_name}[/]")
    scan_table.add_row("  Framework", f"[bold #10B981]{framework}[/]")
    scan_table.add_row("  Provider",  f"[#F0F0FF]{provider}[/]" + (f" [dim]({model})[/]" if model else ""))
    scan_table.add_row("  Code size", f"{len(code):,} chars")
    scan_table.add_row("  API files", str(len(api_files)))
    console.print(scan_table)
    console.print()

    # Show detected files (max 8)
    for f in api_files[:8]:
        console.print(f"  [dim]▸[/] [#6C63FF]{f.name}[/]")
        time.sleep(0.04)
    if len(api_files) > 8:
        console.print(f"  [dim]  … and {len(api_files) - 8} more[/]")
    console.print()

    # ── Phase 2: Analyze + Import (animated progress) ─────────────────────────
    console.print(Rule("[bold #6C63FF]  Analyzing  ", style="#6C63FF"))
    console.print()

    t_start = time.monotonic()
    result: dict = {}

    PHASES = [
        (33,  "[#6C63FF]Parsing routes…[/]"),
        (66,  "[#6C63FF]Building collection…[/]"),
        (90,  "[#6C63FF]Importing to Postman…[/]"),
        (100, "[#10B981]Complete![/]"),
    ]

    try:
        with Progress(
            SpinnerColumn(spinner_name="dots", style="bold #6C63FF"),
            TextColumn("{task.description}"),
            BarColumn(
                bar_width=36,
                style="#6C63FF",
                complete_style="#10B981",
                finished_style="#10B981",
            ),
            TextColumn("[bold #F0F0FF]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            task = progress.add_task(PHASES[0][1], total=100)

            import threading

            def _run() -> None:
                result.update(asyncio.run(_run_agent(
                    code, project_name, args.base_url, args.token,
                    getattr(args, "ai", False), provider, model,
                )))

            thread = threading.Thread(target=_run, daemon=True)
            thread.start()

            phase_idx = 0
            while thread.is_alive():
                elapsed_frac = min((time.monotonic() - t_start) / 120, 0.88)  # cap at 88% while running
                simulated = int(elapsed_frac * 90)
                if phase_idx < len(PHASES) - 1 and simulated >= PHASES[phase_idx][0]:
                    phase_idx += 1
                progress.update(task, completed=simulated, description=PHASES[phase_idx][1])
                time.sleep(0.12)

            thread.join()
            # Smooth fill to 100
            current_pct = int(progress.tasks[0].completed)
            for pct in range(current_pct, 101, 2):
                progress.update(task, completed=pct, description=PHASES[-1][1])
                time.sleep(0.03)

    except Exception as e:
        console.print(f"  [red]✗[/]  Agent error: {e}")
        sys.exit(1)

    elapsed = time.monotonic() - t_start
    console.print()
    _print_result(
        result.get("routes", []),
        result.get("postman_collection", {}),
        result.get("postman_import", {}),
        args,
        elapsed,
    )


def watch_command(args: argparse.Namespace) -> None:
    _print_banner()
    _load_env()

    provider = getattr(args, "provider", None) or os.getenv("LLM_PROVIDER", "groq")
    model = getattr(args, "model", None) or os.getenv("LLM_MODEL", "")

    _check_provider_key(provider)

    if not os.getenv("POSTMAN_API_KEY"):
        console.print("[red]✗[/] POSTMAN_API_KEY not found. Run: [bold cyan]postman-agent setup[/]")
        sys.exit(1)

    scan_path = Path(args.scan).resolve()
    if not scan_path.exists() or not scan_path.is_dir():
        console.print(f"[red]✗[/] Directory not found: {args.scan}")
        sys.exit(1)

    console.print(f"[cyan]✓[/] Watching: {scan_path}")
    console.print("[dim]Press Ctrl+C to stop[/]\n")

    def _get_snapshot() -> dict[str, float]:
        return {
            str(f): f.stat().st_mtime
            for ext in (".js", ".ts", ".py")
            for f in scan_path.rglob(f"*{ext}")
            if not any(ex in f.parts for ex in _EXCLUDED_DIRS) and _is_api_file(f)
        }

    def _run_once() -> None:
        code, project_name, api_files = _scan_code(args)
        info_table = Table(show_header=False, box=None)
        info_table.add_row("[dim]Framework[/]", _detect_framework(code))
        info_table.add_row("[dim]Code size[/]", f"{len(code):,} chars")
        console.print(info_table)
        console.print("\n[#6C63FF]Analyzing code…[/]\n")
        try:
            t0 = time.monotonic()
            result = asyncio.run(_run_agent(
                code, project_name, args.base_url, args.token,
                getattr(args, "ai", False), provider, model,
            ))
            _print_result(
                result.get("routes", []),
                result.get("postman_collection", {}),
                result.get("postman_import", {}),
                args,
                time.monotonic() - t0,
            )
            console.print("  [dim]Watching for changes…[/]\n")
        except Exception as e:
            console.print(f"  [red]✗[/]  {e}")

    snapshot = _get_snapshot()
    _run_once()

    try:
        while True:
            time.sleep(args.interval)
            new_snapshot = _get_snapshot()
            if new_snapshot != snapshot:
                changed = [
                    Path(f).name for f in new_snapshot
                    if new_snapshot.get(f) != snapshot.get(f) or f not in snapshot
                ]
                console.print(f"[yellow]⚠[/] Change detected in: {', '.join(changed)}")
                snapshot = new_snapshot
                _run_once()
    except KeyboardInterrupt:
        console.print("\n[cyan]✓[/] Watch mode stopped.")


def _add_provider_model_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--provider", "-p", default=None,
                   help="LLM provider (groq, gemini, glm, ollama, cerebras, sambanova, "
                        "cloudflare, together, fireworks, huggingface, openrouter, "
                        "openai, anthropic, mistral, cohere)")
    p.add_argument("--model", "-m", default=None,
                   help="Model name (overrides LLM_MODEL env var)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Postman AI Agent -- Auto-generate Postman Collections from backend code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  postman-agent setup
  postman-agent providers
  postman-agent models --provider groq
  postman-agent generate --file routes.js
  postman-agent generate --scan .
  postman-agent generate --scan . --provider gemini
  postman-agent generate --scan . --provider ollama --model deepseek-r1
        """,
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("setup", help="Configure LLM provider and API keys")
    subparsers.add_parser("providers", help="List all available LLM providers")

    mdl = subparsers.add_parser("models", help="List models for a specific provider")
    mdl.add_argument("--provider", "-p", required=True, help="Provider name")

    gen = subparsers.add_parser("generate", help="Generate Postman Collection")
    gen.add_argument("--file", "-f", help="Path to a single route file")
    gen.add_argument("--scan", "-s", help="Scan a directory for API files")
    gen.add_argument("--base-url", "-b", default="http://localhost:3000",
                     help="Base URL for API requests (default: http://localhost:3000)")
    gen.add_argument("--token", "-t", default="your_jwt_token_here",
                     help="JWT token value (default: your_jwt_token_here)")
    gen.add_argument("--name", "-n", default=None,
                     help="Override collection name (default: auto from project folder)")
    gen.add_argument("--output", "-o", default=None,
                     help="Save collection as JSON file (e.g. --output collection.json)")
    gen.add_argument("--dry-run", "-d", action="store_true",
                     help="Preview routes without importing to Postman")
    gen.add_argument("--ai", action="store_true",
                     help="Force AI enhancement even for large projects (>100 routes)")
    _add_provider_model_args(gen)

    watch = subparsers.add_parser("watch", help="Watch directory and auto re-generate on file changes")
    watch.add_argument("--scan", "-s", required=True, help="Directory to watch")
    watch.add_argument("--base-url", "-b", default="http://localhost:3000",
                       help="Base URL for API requests")
    watch.add_argument("--token", "-t", default="your_jwt_token_here", help="JWT token value")
    watch.add_argument("--name", "-n", default=None, help="Override collection name")
    watch.add_argument("--output", "-o", default=None,
                       help="Save collection as JSON file on each change")
    watch.add_argument("--interval", default=3, type=int,
                       help="Poll interval in seconds (default: 3)")
    watch.add_argument("--file", default=None, help=argparse.SUPPRESS)
    watch.add_argument("--ai", action="store_true", help=argparse.SUPPRESS)
    _add_provider_model_args(watch)

    args = parser.parse_args()

    if args.command == "setup":
        setup_command(args)
    elif args.command == "providers":
        providers_command(args)
    elif args.command == "models":
        models_command(args)
    elif args.command == "generate":
        generate_command(args)
    elif args.command == "watch":
        watch_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
