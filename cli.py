"""Typer-based CLI orchestration for AutoPahe."""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import typer

from ap_core.config import load_app_config, sample_config_text, write_sample_config
from state import AutoPaheState


app = typer.Typer(
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="AutoPahe - Anime downloader with advanced features",
)


def get_core_module():
    """Resolve active core module for script and entrypoint execution modes."""
    main_mod = sys.modules.get("__main__")
    if main_mod is not None and hasattr(main_mod, "command_main"):
        return main_mod

    import auto_pahe as core_module

    return core_module


def _split_option_values(raw_value: Optional[str]) -> Optional[list[str]]:
    if raw_value is None:
        return None
    if raw_value == "":
        return []
    return [item for item in raw_value.split("\x1f") if item]


def _normalize_cli_argv(argv: list[str]) -> list[str]:
    """Normalize legacy flags for Typer/Click parsing compatibility."""
    if not argv:
        return argv

    normalized = [argv[0]]
    i = 1

    while i < len(argv):
        token = argv[i]

        if token == "-md":
            token = "--multi_download"
        elif token == "-st":
            token = "--stream"
        elif token == "-dt":
            token = "--execution_data"
        elif token == "-ml":
            token = "--multilinks"

        if token in ("-R", "--records", "--collection"):
            option_name = "--records" if token in ("-R", "--records") else "--collection"
            normalized.append(option_name)
            i += 1
            values = []
            while i < len(argv) and not argv[i].startswith("-"):
                values.append(argv[i])
                i += 1
            normalized.append("\x1f".join(values))
            continue

        if token == "--write-config":
            normalized.append(token)
            if i + 1 >= len(argv) or argv[i + 1].startswith("-"):
                normalized.append("")
                i += 1
                continue

            i += 1
            normalized.append(argv[i])
            i += 1
            continue

        normalized.append(token)
        i += 1

    return normalized


def _handle_config_command(remaining: list[str], config_path: Optional[str], cfg_path: Optional[str]) -> bool:
    """Handle legacy config command workflow. Returns True when handled."""
    if not remaining or str(remaining[0]) != "config":
        return False

    sub = str(remaining[1]) if len(remaining) >= 2 else "edit"
    extra = [str(x) for x in (remaining[2:] if len(remaining) >= 3 else [])]

    from ap_core.platform_paths import get_config_dir

    default_path = get_config_dir() / "config.ini"
    if config_path:
        target_path = Path(config_path).expanduser()
    elif cfg_path:
        target_path = Path(cfg_path)
    else:
        target_path = default_path

    if sub in {"edit", ""}:
        if extra and extra[0] in {"show", "print"}:
            try:
                if target_path.exists():
                    print(target_path.read_text(encoding="utf-8"))
                else:
                    print(sample_config_text())
            except Exception as exc:
                print(f"ERROR: Failed to read config: {exc}", file=sys.stderr)
            return True

        if extra and extra[0] in {"validate", "check"}:
            cfg2, cfg2_path, warns2 = load_app_config(str(target_path) if target_path else None)
            if cfg2_path:
                print(f"Config file: {cfg2_path}")
            else:
                print("Config file: (none found; using defaults)")
            for warning in (warns2 or []):
                print(f"WARNING: {warning}", file=sys.stderr)
            for key in sorted(cfg2.keys()):
                print(f"{key} = {cfg2[key]}")
            return True

        try:
            if not target_path.exists():
                write_sample_config(str(target_path))

            from ap_core.platform_paths import is_windows

            if is_windows():
                editor = os.environ.get("EDITOR") or "notepad"
            else:
                editor = os.environ.get("EDITOR") or "vi"

            if is_windows() and editor.lower() == "notepad":
                subprocess.call([editor, str(target_path)])
            else:
                subprocess.call(shlex.split(editor) + [str(target_path)])
        except Exception as exc:
            print(f"ERROR: Failed to open editor: {exc}", file=sys.stderr)
            print(f"Config file location: {target_path}", file=sys.stderr)
            print("You can manually edit this file with any text editor.", file=sys.stderr)
        return True

    if sub in {"show"}:
        try:
            if target_path.exists():
                print(target_path.read_text(encoding="utf-8"))
            else:
                print(sample_config_text())
        except Exception as exc:
            print(f"ERROR: Failed to read config: {exc}", file=sys.stderr)
        return True

    if sub in {"validate", "check"}:
        cfg2, cfg2_path, warns2 = load_app_config(str(target_path) if target_path else None)
        if cfg2_path:
            print(f"Config file: {cfg2_path}")
        else:
            print("Config file: (none found; using defaults)")
        for warning in (warns2 or []):
            print(f"WARNING: {warning}", file=sys.stderr)
        for key in sorted(cfg2.keys()):
            print(f"{key} = {cfg2[key]}")
        return True

    print("ERROR: Unknown config subcommand. Use: autopahe config edit|show|validate", file=sys.stderr)
    return True


@app.callback(invoke_without_command=True)
def cli_main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "-v", "--version", help="Display AutoPahe version and exit"),
    browser: Optional[str] = typer.Option(None, "-b", "--browser", help="Select Playwright browser"),
    search: Optional[str] = typer.Option(None, "-s", "--search", help="Search for an anime by name"),
    index: Optional[int] = typer.Option(None, "-i", "--index", help="Specify the index of the desired anime from the search results"),
    single_download: Optional[int] = typer.Option(None, "-d", "--single_download", "--single-download", help="Prepare a browser download for a single episode"),
    multi_download: Optional[str] = typer.Option(None, "--multi_download", "--multi-download", help="Prepare browser downloads for multiple episodes (e.g., 1-12)"),
    stream: Optional[str] = typer.Option(None, "--stream", help="Stream episode instead of downloading (e.g., 1 or 1-3)"),
    player: str = typer.Option("default", "--player", help="Media player for streaming (default: auto-detect)"),
    link: Optional[str] = typer.Option(None, "-l", "--link", help="Display the link to the kwik download page"),
    multilinks: Optional[str] = typer.Option(None, "--multilinks", help="Display multiple links to the kwik download pages"),
    about_flag: bool = typer.Option(False, "-a", "--about", help="Output an overview of the anime"),
    resolution: Optional[str] = typer.Option(None, "-p", "--resolution", help="Video resolution for downloads"),
    workers: Optional[int] = typer.Option(None, "-w", "--workers", help="Number of parallel workers for multi-episode downloads (use >1 with caution)"),
    record: Optional[str] = typer.Option(None, "-r", "--record", help="Interact with the records/database (view, [index], [keyword])"),
    records_raw: Optional[str] = typer.Option(None, "--records", help="Robust records management command values"),
    sort: Optional[str] = typer.Option(None, "--sort", help="Sort downloaded files (integrates pahesort)"),
    sort_path: Optional[str] = typer.Option(None, "--sort-path", help="Path to sort; defaults to Downloads"),
    sort_dry_run: bool = typer.Option(False, "--sort-dry-run", help="Dry-run sorting (no changes)"),
    summary: Optional[str] = typer.Option(None, "--summary", help="Show execution stats and records summary"),
    year: Optional[int] = typer.Option(None, "--year", help="Filter search results by year (e.g., 2020)"),
    status: Optional[str] = typer.Option(None, "--status", help='Filter search results by status (e.g., "Finished Airing")'),
    season: Optional[int] = typer.Option(None, "--season", help="Download entire season (12-13 eps). Example: --season 1 downloads eps 1-12"),
    notify: bool = typer.Option(False, "--notify", help="Enable desktop notifications on download complete/fail"),
    dub: bool = typer.Option(False, "--dub", help="Prefer English dubbed versions (default: subbed)"),
    cache: Optional[str] = typer.Option(None, "--cache", help="Cache management: clear (remove all) or stats (show info)"),
    setup: bool = typer.Option(False, "--setup", help="Initial setup: write config and install browser"),
    update: bool = typer.Option(False, "--update", help="Update AutoPahe and refresh dependencies"),
    no_fuzzy: bool = typer.Option(False, "--no-fuzzy", help="Disable fuzzy search (exact match only)"),
    fuzzy_threshold: float = typer.Option(0.6, "--fuzzy-threshold", help="Fuzzy search similarity threshold (0.0-1.0, default: 0.6)"),
    resume: bool = typer.Option(False, "--resume", help="Resume interrupted downloads from previous session"),
    resume_stats: bool = typer.Option(False, "--resume-stats", help="Show download resume statistics"),
    max_retries: int = typer.Option(3, "--max-retries", help="Maximum retry attempts for failed downloads (default: 3)"),
    collection_raw: Optional[str] = typer.Option(None, "--collection", help="Collection management command values"),
    collection_path: Optional[str] = typer.Option(None, "--collection-path", help="Path for collection operations (export/import file path)"),
    watch_status: Optional[str] = typer.Option(None, "--watch-status", help="Update watch status for an anime (use with -s and -i)"),
    watch_progress: Optional[int] = typer.Option(None, "--watch-progress", help="Update watch progress (episodes watched) for an anime"),
    rate: Optional[int] = typer.Option(None, "--rate", help="Rate an anime (1-10, use with -s and -i)"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging (DEBUG level)"),
    quiet: bool = typer.Option(False, "--quiet", help="Minimal logging (WARNING level only)"),
    config: Optional[str] = typer.Option(None, "--config", help="Path to a config INI file"),
    write_config: Optional[str] = typer.Option(None, "--write-config", help="Write a sample config to the given path (or default) and exit"),
    execution_data: Optional[str] = typer.Option(None, "--execution_data", "--execution-data", help="Retrieve execution data for a specific date or date range."),
):
    core = get_core_module()
    start_time = time.perf_counter()
    if ctx.obj is None:
        ctx.obj = AutoPaheState()

    cfg, cfg_path, cfg_warnings = load_app_config(config)
    for warning in (cfg_warnings or []):
        try:
            print(f"WARNING: {warning}", file=sys.stderr)
        except Exception:
            pass

    if write_config is not None:
        from ap_core.platform_paths import get_config_dir

        default_path = str(get_config_dir() / "config.ini")
        target = write_config or default_path
        written = write_sample_config(target)
        print(f"Sample config written to: {written}")
        return

    remaining = list(ctx.args)
    if _handle_config_command(remaining, config, cfg_path):
        return

    core.APP_CONFIG = cfg

    default_browser = cfg.get("browser", "chrome")
    if not cfg.get("browser") and os.environ.get("AUTOPAHE_BROWSER"):
        default_browser = os.environ.get("AUTOPAHE_BROWSER")

    effective_browser = browser or default_browser
    effective_resolution = resolution or str(cfg.get("resolution", "720"))
    effective_workers = workers if workers is not None else int(cfg.get("workers", "1"))

    if version:
        print(f"AutoPahe v{core.AUTOPAHE_VERSION}")
        print("⚡ Anime Downloader with Advanced Features ⚡")
        return

    try:
        os.environ["AUTOPAHE_BROWSER"] = effective_browser
    except Exception:
        pass

    if setup:
        core.setup_environment()
        return

    if update:
        from ap_core.updater import self_update

        raise typer.Exit(self_update())

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Verbose logging enabled")
        if cfg_path:
            logging.debug(f"Config loaded from: {cfg_path}")
        else:
            logging.debug("No config file found, using defaults")
        logging.debug(
            f"Config values: browser={cfg.get('browser')}, resolution={cfg.get('resolution')}, workers={cfg.get('workers')}"
        )
        logging.debug(f"Effective resolution: {effective_resolution}")
    elif quiet:
        logging.getLogger().setLevel(logging.WARNING)
    else:
        logging.getLogger().setLevel(logging.ERROR)

    records_cmd = _split_option_values(records_raw)
    collection_cmd = _split_option_values(collection_raw)

    args = SimpleNamespace(
        version=version,
        browser=effective_browser,
        search=search,
        index=index,
        single_download=single_download,
        multi_download=multi_download,
        stream=stream,
        player=player,
        link=link,
        multilinks=multilinks,
        about=about_flag,
        resolution=effective_resolution,
        workers=effective_workers,
        record=record,
        records=records_cmd,
        sort=sort,
        sort_path=sort_path,
        sort_dry_run=sort_dry_run,
        summary=summary,
        year=year,
        status=status,
        season=season,
        notify=notify,
        dub=dub,
        cache=cache,
        setup=setup,
        update=update,
        no_fuzzy=no_fuzzy,
        fuzzy_threshold=fuzzy_threshold,
        resume=resume,
        resume_stats=resume_stats,
        max_retries=max_retries,
        collection=collection_cmd,
        collection_path=collection_path,
        watch_status=watch_status,
        watch_progress=watch_progress,
        rate=rate,
        verbose=verbose,
        quiet=quiet,
        config=config,
        write_config=write_config,
        execution_data=execution_data,
    )

    has_action = any(
        [
            bool(args.search),
            args.index is not None,
            args.single_download is not None,
            bool(args.multi_download),
            bool(args.stream),
            bool(args.link),
            bool(args.multilinks),
            bool(args.about),
            bool(args.record),
            bool(args.records),
            bool(args.sort),
            bool(args.sort_path),
            bool(args.sort_dry_run),
            bool(args.cache),
            bool(args.update),
            bool(args.summary),
            args.year is not None,
            bool(args.status),
            args.season is not None,
            bool(args.notify),
            bool(args.execution_data),
            bool(args.resume),
            bool(args.resume_stats),
            args.collection is not None,
            bool(args.watch_status),
            args.watch_progress is not None,
            args.rate is not None,
        ]
    )

    if has_action:
        try:
            core.Banners.header()
        except Exception:
            pass
        core.command_main(args, ctx)
    else:
        try:
            os.system("cls" if os.name == "nt" else "clear")
        except Exception:
            pass
        try:
            core.Banners.header()
        except Exception:
            pass
        print("\nNo arguments provided. Try these options:\n")
        print("  📺 BASIC OPERATIONS:")
        print("  -s, --search <query>          Search for anime (typos auto-corrected!)")
        print("  -i, --index <n>               Select anime index from search results")
        print("  -d, --single_download <ep>    Prepare a browser download for one episode")
        print("  -md, --multi_download <spec>  Prepare browser downloads (e.g., 1-5 or 1,3,5)")
        print("  -a, --about                   Show anime overview")
        print("  -p, --resolution <720|1080>   Choose resolution")
        print("  -w, --workers <n>             Parallel downloads (use >1 with caution)")
        print("\n  🎯 SMART FEATURES (NEW!):")
        print("      --no-fuzzy                Disable fuzzy search (exact match only)")
        print("      --resume                  Resume interrupted downloads")
        print("      --resume-stats            Show download resume statistics")
        print("      --collection stats        View your anime collection statistics")
        print("      --collection organize     Organize collection files into folders")
        print("      --collection duplicates   Find and remove duplicate files")
        print("      --watch-status <status>   Update watch status (watching/completed/etc)")
        print("      --rate <1-10>             Rate an anime")
        print("\n  🔧 MANAGEMENT:")
        print("  -R, --records [...]           Manage records (view/search/delete/...)")
        print("      --sort [all|rename|organize]  Sort downloaded files")
        print("      --cache [clear|stats]     Manage cache and cookies")
        print("      --update                  Update AutoPahe and refresh dependencies")
        print("      --year <YYYY>             Filter by year")
        print("      --status <text>           Filter by status (e.g., Finished Airing)")
        print("      --season <n>              Download a whole season (12-13 eps)")
        print("      --notify                  Enable desktop notifications")
        print("      --verbose | --quiet       Adjust logging verbosity\n")
        print("Launching Interactive Mode...\n")
        core.interactive_main()

    elapsed = time.perf_counter() - start_time
    if elapsed > 0.5:
        logging.debug(f"Execution completed in {elapsed:.2f} seconds")


def run() -> None:
    """Entrypoint used by auto_pahe.main."""
    sys.argv = _normalize_cli_argv(sys.argv)
    app(obj=AutoPaheState())
