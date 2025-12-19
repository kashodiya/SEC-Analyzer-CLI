"""Main CLI interface for SEC Analyzer."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import asyncio
from typing import Optional

from .config import Config
from .sec_client import SECClient
from .risk_analyzer import RiskAnalyzer
from .report_generator import ReportGenerator
from .cache_manager import CacheManager

console = Console()


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx):
    """SEC Analyzer - Assess company risks from SEC reports using AI."""
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config()


@cli.command()
@click.argument('ticker', type=str)
@click.option('--report-type', '-t', 
              type=click.Choice(['10-K', '10-Q', '8-K', 'all']), 
              default='10-K',
              help='Type of SEC report to analyze')
@click.option('--output', '-o', 
              type=click.Path(), 
              help='Output file for the analysis report')
@click.option('--verbose', '-v', 
              is_flag=True, 
              help='Enable verbose output')
@click.pass_context
def analyze(ctx, ticker: str, report_type: str, output: Optional[str], verbose: bool):
    """Analyze SEC reports for a company ticker symbol."""
    config = ctx.obj['config']
    
    console.print(Panel(
        f"[bold blue]SEC Risk Analysis[/bold blue]\n"
        f"Company: {ticker.upper()}\n"
        f"Report Type: {report_type}",
        title="Analysis Started"
    ))
    
    asyncio.run(_run_analysis(config, ticker, report_type, output, verbose))


async def _run_analysis(config: Config, ticker: str, report_type: str, 
                       output: Optional[str], verbose: bool):
    """Run the complete analysis workflow."""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Initialize components
        task1 = progress.add_task("Initializing SEC client...", total=None)
        sec_client = SECClient(config)
        await sec_client.initialize()
        
        task2 = progress.add_task("Initializing AI risk analyzer...", total=None)
        risk_analyzer = RiskAnalyzer(config)
        await risk_analyzer.initialize()
        
        progress.update(task1, completed=True)
        progress.update(task2, completed=True)
        
        # Fetch SEC reports
        task3 = progress.add_task(f"Fetching {report_type} reports for {ticker}...", total=None)
        try:
            reports = await sec_client.get_company_reports(ticker, report_type)
            progress.update(task3, completed=True)
            
            if not reports:
                console.print(f"[red]No {report_type} reports found for {ticker}[/red]")
                return
                
        except Exception as e:
            progress.update(task3, completed=True)
            console.print(f"[red]Error fetching reports: {e}[/red]")
            return
        
        # Analyze risks
        task4 = progress.add_task("Analyzing risks with AI agent...", total=None)
        try:
            analysis_results = await risk_analyzer.analyze_reports(reports, ticker, report_type)
            progress.update(task4, completed=True)
        except Exception as e:
            progress.update(task4, completed=True)
            console.print(f"[red]Error during analysis: {e}[/red]")
            return
        
        # Generate report
        task5 = progress.add_task("Generating analysis report...", total=None)
        report_generator = ReportGenerator(config)
        report = report_generator.generate_report(analysis_results, ticker, report_type)
        progress.update(task5, completed=True)
    
    # Display results
    _display_results(analysis_results, ticker)
    
    # Save to file if requested
    if output:
        with open(output, 'w') as f:
            f.write(report)
        console.print(f"[green]Report saved to {output}[/green]")


def _display_results(results: dict, ticker: str):
    """Display analysis results in a formatted table."""
    
    # Risk Summary Table
    risk_table = Table(title=f"Risk Assessment Summary - {ticker.upper()}")
    risk_table.add_column("Risk Category", style="cyan")
    risk_table.add_column("Level", style="magenta")
    risk_table.add_column("Score", justify="right", style="green")
    risk_table.add_column("Key Concerns", style="yellow")
    
    for category, data in results.get('risk_categories', {}).items():
        risk_table.add_row(
            category.title(),
            data.get('level', 'Unknown'),
            str(data.get('score', 'N/A')),
            data.get('summary', 'No concerns identified')[:50] + "..."
        )
    
    console.print(risk_table)
    
    # Key Insights
    if 'key_insights' in results:
        console.print("\n[bold]Key Insights:[/bold]")
        for insight in results['key_insights'][:5]:  # Show top 5
            console.print(f"• {insight}")
    
    # Overall Risk Score
    overall_score = results.get('overall_risk_score', 'N/A')
    risk_level = results.get('overall_risk_level', 'Unknown')
    
    console.print(Panel(
        f"[bold]Overall Risk Score: {overall_score}[/bold]\n"
        f"Risk Level: {risk_level}",
        title="Summary",
        border_style="green" if risk_level.lower() == "low" else "yellow" if risk_level.lower() == "medium" else "red"
    ))


@cli.command()
@click.argument('ticker', type=str)
@click.option('--limit', '-l', default=5, help='Number of recent filings to show')
@click.pass_context
def filings(ctx, ticker: str, limit: int):
    """List recent SEC filings for a company."""
    config = ctx.obj['config']
    
    console.print(f"[bold]Recent SEC Filings for {ticker.upper()}[/bold]")
    
    asyncio.run(_list_filings(config, ticker, limit))


async def _list_filings(config: Config, ticker: str, limit: int):
    """List recent filings for a company."""
    sec_client = SECClient(config)
    await sec_client.initialize()
    
    try:
        filings = await sec_client.get_recent_filings(ticker, limit)
        
        if not filings:
            console.print(f"[red]No filings found for {ticker}[/red]")
            return
        
        table = Table()
        table.add_column("Date", style="cyan")
        table.add_column("Form Type", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("URL", style="blue")
        
        for filing in filings:
            table.add_row(
                filing.get('date', 'N/A'),
                filing.get('form_type', 'N/A'),
                filing.get('description', 'N/A')[:50] + "...",
                filing.get('url', 'N/A')[:50] + "..."
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error fetching filings: {e}[/red]")


@cli.command()
def config():
    """Show current configuration."""
    config_obj = Config()
    
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("AWS Region", config_obj.aws_region)
    table.add_row("Bedrock Model", config_obj.bedrock_model)
    table.add_row("User Agent", config_obj.user_agent)
    table.add_row("SEC API Rate Limit", str(config_obj.sec_api_rate_limit))
    table.add_row("Max Report Length", str(config_obj.max_report_length))
    table.add_row("Cache Enabled", str(config_obj.cache_enabled))
    table.add_row("Cache DB Path", config_obj.cache_db_path)
    table.add_row("Cache Expiry Days", str(config_obj.cache_expiry_days))
    table.add_row("Cache Compression", str(config_obj.cache_compression))
    table.add_row("Cache Max Size (MB)", str(config_obj.cache_max_size_mb))
    
    console.print(table)


@cli.group()
def cache():
    """Cache management commands."""
    pass


@cache.command()
@click.pass_context
def stats(ctx):
    """Show cache statistics."""
    config_obj = ctx.obj['config']
    asyncio.run(_show_cache_stats(config_obj))


@cache.command()
@click.option('--table', type=click.Choice(['company_ciks', 'filing_metadata', 'document_content', 'analysis_results', 'all']), 
              default='all', help='Table to clear (default: all)')
@click.confirmation_option(prompt='Are you sure you want to clear the cache?')
@click.pass_context
def clear(ctx, table):
    """Clear cache data."""
    config_obj = ctx.obj['config']
    asyncio.run(_clear_cache(config_obj, table))


@cache.command()
@click.pass_context
def cleanup(ctx):
    """Remove expired cache entries."""
    config_obj = ctx.obj['config']
    asyncio.run(_cleanup_cache(config_obj))


async def _show_cache_stats(config: Config):
    """Show cache statistics."""
    cache_manager = CacheManager(config)
    await cache_manager.initialize()
    
    stats = await cache_manager.get_cache_stats()
    
    if not stats.get('cache_enabled', False):
        console.print("[yellow]Cache is disabled[/yellow]")
        return
    
    table = Table(title="Cache Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Cache Enabled", str(stats.get('cache_enabled', False)))
    table.add_row("Database Size", f"{stats.get('db_size_mb', 0)} MB")
    table.add_row("Company CIKs", str(stats.get('company_ciks_count', 0)))
    table.add_row("Filing Metadata", str(stats.get('filing_metadata_count', 0)))
    table.add_row("Document Content", str(stats.get('document_content_count', 0)))
    table.add_row("Analysis Results", str(stats.get('analysis_results_count', 0)))
    
    if stats.get('oldest_entry'):
        table.add_row("Oldest Entry", stats['oldest_entry'])
    if stats.get('newest_entry'):
        table.add_row("Newest Entry", stats['newest_entry'])
    
    console.print(table)


async def _clear_cache(config: Config, table: str):
    """Clear cache data."""
    cache_manager = CacheManager(config)
    await cache_manager.initialize()
    
    if table == 'all':
        await cache_manager.clear_cache()
        console.print("[green]All cache data cleared[/green]")
    else:
        await cache_manager.clear_cache(table)
        console.print(f"[green]Cache table '{table}' cleared[/green]")


@cache.command()
@click.pass_context
def performance(ctx):
    """Show detailed cache performance statistics."""
    config_obj = ctx.obj['config']
    asyncio.run(_show_cache_performance(config_obj))


async def _show_cache_performance(config: Config):
    """Show detailed cache performance statistics."""
    cache_manager = CacheManager(config)
    await cache_manager.initialize()
    
    perf_stats = await cache_manager.get_performance_stats()
    
    if not perf_stats.get('cache_enabled', False):
        console.print("[yellow]Cache is disabled[/yellow]")
        return
    
    # Overall performance
    console.print(Panel(
        f"[bold]Overall Hit Rate:[/bold] {perf_stats.get('overall_hit_rate', 0)}%\n"
        f"[bold]Session Hits:[/bold] {perf_stats.get('session_hits', 0)}\n"
        f"[bold]Session Misses:[/bold] {perf_stats.get('session_misses', 0)}",
        title="Cache Performance Summary"
    ))
    
    # Detailed performance by operation
    performance_data = perf_stats.get('performance', {})
    if performance_data:
        table = Table(title="Performance by Operation")
        table.add_column("Operation", style="cyan")
        table.add_column("Hit Rate", style="green")
        table.add_column("Total Requests", style="blue")
        table.add_column("Avg Response (ms)", style="yellow")
        table.add_column("Last Updated", style="magenta")
        
        for operation, data in performance_data.items():
            table.add_row(
                operation.replace('_', ' ').title(),
                f"{data['hit_rate']}%",
                str(data['total_requests']),
                str(data['avg_response_time_ms']),
                data['last_updated'][:19] if data['last_updated'] else 'N/A'
            )
        
        console.print(table)
    else:
        console.print("[yellow]No performance data available yet[/yellow]")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()


@cache.command()
@click.argument('tickers', nargs=-1, required=True)
@click.option('--report-type', '-t', 
              type=click.Choice(['10-K', '10-Q', '8-K', 'all']), 
              default='10-K',
              help='Type of SEC report to warm cache for')
@click.pass_context
def warm(ctx, tickers, report_type):
    """Warm cache by pre-loading data for specified tickers."""
    config_obj = ctx.obj['config']
    asyncio.run(_warm_cache(config_obj, tickers, report_type))


async def _warm_cache(config: Config, tickers: tuple, report_type: str):
    """Warm cache by pre-loading SEC data."""
    console.print(f"[bold blue]Warming cache for {len(tickers)} companies...[/bold blue]")
    
    sec_client = SECClient(config)
    await sec_client.initialize()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        for ticker in tickers:
            task = progress.add_task(f"Loading data for {ticker}...", total=None)
            
            try:
                # This will cache CIK and filing metadata
                reports = await sec_client.get_company_reports(ticker, report_type)
                progress.update(task, completed=True)
                console.print(f"[green]✓ Cached {len(reports)} reports for {ticker}[/green]")
                
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]✗ Error caching {ticker}: {e}[/red]")
    
    console.print("[bold green]Cache warming completed![/bold green]")

async def _cleanup_cache(config: Config):
    """Remove expired cache entries."""
    cache_manager = CacheManager(config)
    await cache_manager.initialize()
    
    await cache_manager.cleanup_expired_cache()
    console.print("[green]Expired cache entries removed[/green]")