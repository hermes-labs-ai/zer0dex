#!/usr/bin/env python3
"""
zer0dex CLI — Dual-layer memory for AI agents.

Commands:
  zer0dex init     Initialize a new zer0dex memory store
  zer0dex seed     Seed vector store from markdown files
  zer0dex serve    Start the memory server
  zer0dex query    Query memories from the command line
  zer0dex status   Check server health and memory count
  zer0dex add      Add a memory manually
"""
import argparse
import json
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path


DEFAULT_PORT = 18420
DEFAULT_COLLECTION = "zer0dex"
DEFAULT_CHROMA_PATH = ".zer0dex"
DEFAULT_LLM_MODEL = "mistral:7b"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_USER_ID = "agent"

CONFIG_FILE = ".zer0dex.json"


def load_config():
    """Load config from .zer0dex.json if it exists."""
    p = Path(CONFIG_FILE)
    if p.exists():
        return json.loads(p.read_text())
    return {}


def save_config(config):
    """Save config to .zer0dex.json."""
    Path(CONFIG_FILE).write_text(json.dumps(config, indent=2) + "\n")


def cmd_init(args):
    """Initialize a new zer0dex memory store."""
    config = {
        "collection": args.collection or DEFAULT_COLLECTION,
        "chroma_path": args.chroma_path or DEFAULT_CHROMA_PATH,
        "port": args.port or DEFAULT_PORT,
        "user_id": args.user_id or DEFAULT_USER_ID,
        "llm_model": DEFAULT_LLM_MODEL,
        "embed_model": DEFAULT_EMBED_MODEL,
        "ollama_url": DEFAULT_OLLAMA_URL,
    }
    save_config(config)
    Path(config["chroma_path"]).mkdir(parents=True, exist_ok=True)

    print(f"✅ zer0dex initialized")
    print(f"   Collection: {config['collection']}")
    print(f"   Storage: {config['chroma_path']}")
    print(f"   Config: {CONFIG_FILE}")
    print(f"\nNext: zer0dex seed --source your-docs/")


def cmd_seed(args):
    """Seed the vector store from files."""
    config = load_config()
    # Import here to avoid slow startup for other commands
    from zer0dex.seed import collect_files, chunk_markdown

    try:
        from mem0 import Memory
    except ImportError:
        print("Error: mem0 not installed. Run: pip install mem0ai")
        sys.exit(1)

    mem_config = {
        "llm": {"provider": "ollama", "config": {"model": config.get("llm_model", DEFAULT_LLM_MODEL), "ollama_base_url": config.get("ollama_url", DEFAULT_OLLAMA_URL)}},
        "embedder": {"provider": "ollama", "config": {"model": config.get("embed_model", DEFAULT_EMBED_MODEL), "ollama_base_url": config.get("ollama_url", DEFAULT_OLLAMA_URL)}},
        "vector_store": {"provider": "chroma", "config": {"collection_name": config.get("collection", DEFAULT_COLLECTION), "path": config.get("chroma_path", DEFAULT_CHROMA_PATH)}},
    }

    files = collect_files(args.source)
    if not files:
        print("No files found. Use --source <path>")
        sys.exit(1)

    print(f"Found {len(files)} file(s)")
    all_chunks = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        chunks = chunk_markdown(text)
        all_chunks.extend(chunks)
        print(f"  {f.name}: {len(chunks)} chunks")

    if args.dry_run:
        print(f"\n[DRY RUN] Would seed {len(all_chunks)} chunks. Exiting.")
        return

    print(f"\nLoading mem0...")
    memory = Memory.from_config(mem_config)
    user_id = config.get("user_id", DEFAULT_USER_ID)

    total = 0
    for i, chunk in enumerate(all_chunks, 1):
        print(f"  Seeding {i}/{len(all_chunks)}...", end=" ", flush=True)
        result = memory.add(chunk, user_id=user_id)
        n = len(result.get("results", []))
        total += n
        print(f"({n} memories)")

    all_mem = memory.get_all(user_id=user_id)
    final = len(all_mem.get("results", []))
    print(f"\n✅ Seeded {total} memories. Total in store: {final}")


def cmd_check(args):
    """Validate prerequisites before init or seed."""
    config = load_config()
    ollama_url = config.get("ollama_url", DEFAULT_OLLAMA_URL)
    llm_model = config.get("llm_model", DEFAULT_LLM_MODEL)
    embed_model = config.get("embed_model", DEFAULT_EMBED_MODEL)
    all_ok = True

    # 1. Ollama running
    try:
        resp = urllib.request.urlopen(f"{ollama_url}/api/tags", timeout=5)
        tags_data = json.loads(resp.read())
        print(f"✅ Ollama is running at {ollama_url}")

        # 2. Required models present
        available = [m.get("name", "") for m in tags_data.get("models", [])]
        for model in [embed_model, llm_model]:
            # Match by prefix (e.g. "mistral:7b" matches "mistral:7b-instruct")
            found = any(m == model or m.startswith(model.split(":")[0] + ":") for m in available)
            if found:
                print(f"✅ Model present: {model}")
            else:
                print(f"❌ Model missing: {model}  (run: ollama pull {model})")
                all_ok = False

    except urllib.error.URLError:
        print(f"❌ Ollama not reachable at {ollama_url}  (run: ollama serve)")
        print(f"❌ Model check skipped: {embed_model}")
        print(f"❌ Model check skipped: {llm_model}")
        all_ok = False

    # 3. mem0ai importable
    try:
        import mem0  # noqa: F401
        print("✅ mem0ai is importable")
    except ImportError:
        print("❌ mem0ai not installed  (run: pip install mem0ai)")
        all_ok = False

    # 4. chromadb importable
    try:
        import chromadb  # noqa: F401
        print("✅ chromadb is importable")
    except ImportError:
        print("❌ chromadb not installed  (run: pip install chromadb)")
        all_ok = False

    if not all_ok:
        sys.exit(1)


def cmd_serve(args):
    """Start the memory server."""
    config = load_config()
    port = args.port or config.get("port", DEFAULT_PORT)

    # Build server args
    server_args = [
        sys.executable, "-m", "zer0dex.server",
        "--port", str(port),
        "--collection", config.get("collection", DEFAULT_COLLECTION),
        "--chroma-path", config.get("chroma_path", DEFAULT_CHROMA_PATH),
        "--user-id", config.get("user_id", DEFAULT_USER_ID),
        "--llm-model", config.get("llm_model", DEFAULT_LLM_MODEL),
        "--embed-model", config.get("embed_model", DEFAULT_EMBED_MODEL),
        "--ollama-url", config.get("ollama_url", DEFAULT_OLLAMA_URL),
    ]

    if args.background:
        proc = subprocess.Popen(server_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ zer0dex server started (PID {proc.pid}, port {port})")
    else:
        subprocess.run(server_args)


def cmd_query(args):
    """Query the running server."""
    config = load_config()
    port = args.port or config.get("port", DEFAULT_PORT)
    url = f"http://127.0.0.1:{port}/query"
    data = json.dumps({"text": args.text, "limit": args.limit}).encode()

    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=5)
        result = json.loads(resp.read())
        memories = result.get("memories", [])
        if not memories:
            print("No relevant memories found.")
            return
        for m in memories:
            score = m.get("score", 0)
            text = m.get("text", "")
            print(f"  [{score:.3f}] {text}")
    except urllib.error.URLError:
        print(f"Error: zer0dex server not running on port {port}. Run: zer0dex serve")
        sys.exit(1)


def cmd_status(args):
    """Check server health."""
    config = load_config()
    port = args.port or config.get("port", DEFAULT_PORT)
    url = f"http://127.0.0.1:{port}/health"

    try:
        resp = urllib.request.urlopen(url, timeout=3)
        result = json.loads(resp.read())
        print(f"✅ zer0dex running on port {port}")
        print(f"   Memories: {result.get('count', '?')}")
        print(f"   Status: {result.get('status', '?')}")
    except urllib.error.URLError:
        print(f"❌ zer0dex not running on port {port}")
        sys.exit(1)


def cmd_add(args):
    """Add a memory via the server."""
    config = load_config()
    port = args.port or config.get("port", DEFAULT_PORT)
    url = f"http://127.0.0.1:{port}/add"
    data = json.dumps({"text": args.text}).encode()

    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        count = result.get("count", 0)
        memories = result.get("memories", [])
        print(f"✅ Added {count} memory(ies):")
        for m in memories:
            print(f"  • {m}")
    except urllib.error.URLError:
        print(f"Error: zer0dex server not running on port {port}. Run: zer0dex serve")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="zer0dex",
        description="Dual-layer memory for AI agents. 91% recall, 70ms, $0/month.",
    )
    sub = parser.add_subparsers(dest="command")

    # check
    sub.add_parser("check", help="Validate prerequisites (Ollama, models, mem0ai, chromadb)")

    # init
    p_init = sub.add_parser("init", help="Initialize a new memory store")
    p_init.add_argument("--collection", help="Collection name")
    p_init.add_argument("--chroma-path", help="ChromaDB storage path")
    p_init.add_argument("--port", type=int, help="Server port")
    p_init.add_argument("--user-id", help="User ID for memories")

    # seed
    p_seed = sub.add_parser("seed", help="Seed from markdown files")
    p_seed.add_argument("--source", action="append", required=True, help="Source file or directory")
    p_seed.add_argument("--dry-run", action="store_true", help="Show what would be seeded")
    p_seed.add_argument("--port", type=int)

    # serve
    p_serve = sub.add_parser("serve", help="Start memory server")
    p_serve.add_argument("--port", type=int, help="Server port")
    p_serve.add_argument("--background", "-b", action="store_true", help="Run in background")

    # query
    p_query = sub.add_parser("query", help="Query memories")
    p_query.add_argument("text", help="Query text")
    p_query.add_argument("--limit", type=int, default=5, help="Max results")
    p_query.add_argument("--port", type=int)

    # status
    p_status = sub.add_parser("status", help="Check server health")
    p_status.add_argument("--port", type=int)

    # add
    p_add = sub.add_parser("add", help="Add a memory")
    p_add.add_argument("text", help="Memory text")
    p_add.add_argument("--port", type=int)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "check": cmd_check,
        "init": cmd_init,
        "seed": cmd_seed,
        "serve": cmd_serve,
        "query": cmd_query,
        "status": cmd_status,
        "add": cmd_add,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
