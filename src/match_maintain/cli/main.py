"""Match Maintenance CLI — 统一命令行工具，操作 TOML + Git。"""
import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

cli = typer.Typer(name="mm", help="NIKKE PVP 对局数据维护工具", add_completion=False)
console = Console()


def _get_repo():
    from ..config import get_settings
    from ..infrastructure.toml_repository import TOMLRepository
    settings = get_settings()
    return TOMLRepository(settings.matches_path, settings.data_dir)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@cli.command()
def init():
    """初始化 Git 版本控制。"""
    repo = _get_repo()
    if repo.is_git_initialized:
        console.print("[yellow]⚠[/yellow] Git 仓库已初始化")
        return
    repo.git_init()
    console.print("[green]✓[/green] Git 版本控制已初始化")


@cli.command()
def health():
    """检查数据文件状态。"""
    repo = _get_repo()
    try:
        matches, file_hash = _run(repo.read_all())
        console.print(f"[green]✓[/green] 数据文件正常，共 {len(matches)} 条对局")
        if repo.is_git_initialized:
            console.print(f"[green]✓[/green] Git 版本控制已启用")
        else:
            console.print(f"[yellow]⚠[/yellow] Git 未初始化，运行 [bold]mm init[/bold] 启用")
    except Exception as e:
        console.print(f"[red]✗[/red] {e}")


@cli.command()
def list_matches(page: int = typer.Option(1, "--page", "-p", help="页码")):
    """列出对局记录。"""
    repo = _get_repo()
    matches, _ = _run(repo.read_all())
    per_page = 20
    total = len(matches)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    page_matches = matches[start:end]

    table = Table(title=f"对局列表 (第 {page}/{total_pages} 页，共 {total} 条)")
    table.add_column("ID", style="cyan")
    table.add_column("防守方")
    table.add_column("进攻方")
    table.add_column("结果", style="green")
    table.add_column("来源")

    for m in page_matches:
        table.add_row(
            str(m.get("id", "")),
            ", ".join(m.get("defender_team", [])[:3]) + ("..." if len(m.get("defender_team", [])) > 3 else ""),
            ", ".join(m.get("attacker_team", [])[:3]) + ("..." if len(m.get("attacker_team", [])) > 3 else ""),
            m.get("result", ""),
            m.get("source", ""),
        )

    console.print(table)


@cli.command()
def show(match_id: str):
    """查看单条对局详情。"""
    repo = _get_repo()
    try:
        match, _ = _run(repo.read_by_id(match_id))
    except Exception as e:
        console.print(f"[red]✗[/red] {e}")
        return

    console.print(Panel(f"""
ID: {match.get('id')}
结果: {match.get('result')}
来源: {match.get('source')} (trust: {match.get('trust')})
日期: {match.get('date')}
防守方: {', '.join(match.get('defender_team', []))}
进攻方: {', '.join(match.get('attacker_team', []))}
防守爆裂: {_format_burst(match.get('defender_burst', {}))}
进攻爆裂: {_format_burst(match.get('attacker_burst', {}))}
Margin: {match.get('margin')}
Uploader Tag: {match.get('uploader_tag', 'dev')}
Custom Tag: {match.get('custom_def_tag', '')}
Notes: {match.get('notes', 'N/A')}
""", title=f"对局 {match_id}", border_style="green"))


@cli.command()
def search(keyword: str = typer.Argument(..., help="搜索关键词")):
    """按关键词搜索对局。"""
    repo = _get_repo()
    matches, _ = _run(repo.read_all())
    results = []
    for m in matches:
        team_str = " ".join(m.get("defender_team", [])) + " " + " ".join(m.get("attacker_team", []))
        if keyword in team_str or keyword in str(m.get("source", "")) or keyword in str(m.get("notes", "")):
            results.append(m)

    if not results:
        console.print(f"[yellow]未找到[/yellow] 含 '{keyword}' 的对局")
        return

    table = Table(title=f"搜索 '{keyword}' ({len(results)} 条)")
    table.add_column("ID", style="cyan")
    table.add_column("防守方")
    table.add_column("进攻方")
    table.add_column("结果")
    for m in results:
        table.add_row(
            str(m.get("id", "")),
            ", ".join(m.get("defender_team", [])[:3]),
            ", ".join(m.get("attacker_team", [])[:3]),
            m.get("result", ""),
        )
    console.print(table)


@cli.command()
def stats():
    """显示数据统计。"""
    repo = _get_repo()
    matches, _ = _run(repo.read_all())
    sources: dict[str, int] = {}
    results: dict[str, int] = {}
    for m in matches:
        src = m.get("source", "未知")
        sources[src] = sources.get(src, 0) + 1
        r = m.get("result", "未知")
        results[r] = results.get(r, 0) + 1

    console.print(f"[bold]对局统计[/bold]")
    console.print(f"总数: {len(matches)}")
    console.print("\n来源分布:")
    for src, count in sources.items():
        console.print(f"  {src}: {count}")
    console.print("\n结果分布:")
    for r, count in results.items():
        console.print(f"  {r}: {count}")


def _format_burst(burst_data) -> str:
    if not burst_data or not isinstance(burst_data, dict):
        return "N/A"
    parts = []
    for stage in ["B1", "B2", "B3"]:
        chars = burst_data.get(stage, [])
        if chars:
            parts.append(f"{stage}: {', '.join(chars)}")
    return "\n".join(parts) if parts else "N/A"
