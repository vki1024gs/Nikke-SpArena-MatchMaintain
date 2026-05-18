"""Match Maintenance CLI — 命令行工具。"""
import typer
from rich.console import Console
from rich.table import Table

from .client import MatchClient

cli = typer.Typer(name="match", help="NIKKE PVP 对局数据维护 CLI", add_completion=False)
console = Console()


def get_client(base_url: str) -> MatchClient:
    """获取客户端。"""
    return MatchClient(base_url=base_url)


@cli.command()
def health(base_url: str = typer.Option("http://localhost:2771", "--url", "-u")):
    """检查服务健康状态。"""
    client = get_client(base_url)
    try:
        status = client.health()
        console.print(f"[green]✓[/green] {status.get('app', 'Unknown')} v{status.get('version', '?')} - {status.get('status', '?')}")
        console.print(f"   数据文件: {status.get('matches_file', '?')}")
        console.print(f"   时间戳: {status.get('timestamp', '?')}")
    except Exception as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)


@cli.command()
def validate(
    mode: str = typer.Option("quick", "--mode", "-m", help="quick 或 deep"),
    base_url: str = typer.Option("http://localhost:2771", "--url", "-u"),
):
    """验证对局数据。"""
    client = get_client(base_url)

    if mode == "quick":
        result = client.quick_validate()
    else:
        result = client.deep_validate()

    if result.passed:
        console.print("[green]✓[/green] 验证通过")
    else:
        console.print(f"[red]✗[/red] 发现 {len(result.issues)} 个问题")
        for issue in result.issues:
            console.print(f"  - {issue}")
        if result.warnings:
            console.print(f"\n[yellow]⚠[/yellow] {len(result.warnings)} 个警告")


@cli.command()
def fix(
    base_url: str = typer.Option("http://localhost:2771", "--url", "-u"),
):
    """自动修复对局数据问题。"""
    client = get_client(base_url)
    result = client.fix()

    if result.fixed_count > 0:
        console.print(f"[green]✓[/green] 已修复 {result.fixed_count} 处")
        console.print(f"   备份: {result.backup_path}")
    else:
        console.print(f"[yellow]ℹ[/yellow] {result.message}")


@cli.command()
def maintain(
    base_url: str = typer.Option("http://localhost:2771", "--url", "-u"),
):
    """完整维护流程：验证 → 修复 → 归档。"""
    client = get_client(base_url)

    console.print("[bold]开始完整维护流程...[/bold]\n")

    result = client.full_maintenance()

    console.print(f"  验证: {'[green]通过[/green]' if result['validation_passed'] else '[yellow]有警告[/yellow]'}")
    console.print(f"  修复: {result['fix_count']} 处")

    console.print("\n[bold green]✓ 维护完成[/bold green]")


@cli.command()
def list_matches(
    page: int = typer.Option(1, "--page", "-p"),
    base_url: str = typer.Option("http://localhost:2771", "--url", "-u"),
):
    """列出对局记录。"""
    client = get_client(base_url)
    result = client.list_matches(page=page)

    table = Table(title=f"对局列表 (第 {result['page']}/{result['total_pages']} 页，共 {result['total']} 条)")
    table.add_column("ID", style="cyan")
    table.add_column("防守方")
    table.add_column("进攻方")
    table.add_column("结果", style="green")
    table.add_column("来源")

    for m in result.get("matches", []):
        table.add_row(
            str(m.get("id", "?")),
            ", ".join(m.get("defender_team", [])[:3]) + ("..." if len(m.get("defender_team", [])) > 3 else ""),
            ", ".join(m.get("attacker_team", [])[:3]) + ("..." if len(m.get("attacker_team", [])) > 3 else ""),
            m.get("result", "?"),
            m.get("source", "?"),
        )

    console.print(table)


if __name__ == "__main__":
    cli()
