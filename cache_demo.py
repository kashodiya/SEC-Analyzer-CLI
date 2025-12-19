#!/usr/bin/env python3
"""
Enhanced Cache Demo for FRB SEC Analyzer

This script demonstrates the comprehensive caching system with:
- SQLite storage with compression
- Performance tracking and analytics
- Cache warming and management
- Hit rate optimization

Run with: uv run python cache_demo.py
"""

import subprocess
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def run_command(cmd, description=None):
    """Run a CLI command and display results."""
    if description:
        console.print(f"\n[bold blue]{description}[/bold blue]")
    console.print(f"[dim]Command: {cmd}[/dim]")
    console.print("─" * 60)
    
    try:
        result = subprocess.run(
            cmd.split(), 
            capture_output=True, 
            text=True, 
            cwd="."
        )
        
        if result.stdout:
            console.print(result.stdout)
        if result.stderr and "Exit Code:" not in result.stderr:
            console.print(f"[red]{result.stderr}[/red]")
            
    except Exception as e:
        console.print(f"[red]Error running command: {e}[/red]")

def main():
    """Run the comprehensive cache demo."""
    
    console.print(Panel(
        "[bold green]FRB SEC Analyzer - Enhanced Caching System Demo[/bold green]\n\n"
        "This demo showcases the advanced caching features:\n"
        "• SQLite storage with compression\n"
        "• Performance tracking and analytics\n"
        "• Cache warming and management\n"
        "• Hit rate optimization\n"
        "• Automatic cache size management",
        title="Enhanced Cache Demo"
    ))
    
    # 1. Show initial cache state
    run_command("uv run frb-sec-analyzer cache stats", "1. Initial Cache State")
    
    # 2. Show configuration including cache settings
    run_command("uv run frb-sec-analyzer config", "2. Configuration (including cache settings)")
    
    # 3. Warm cache with multiple companies
    console.print("\n[bold]3. Cache Warming - Pre-loading Data[/bold]")
    console.print("Warming cache for major financial institutions...")
    run_command("uv run frb-sec-analyzer cache warm JPM BAC WFC --report-type 10-K")
    
    # 4. Show cache stats after warming
    run_command("uv run frb-sec-analyzer cache stats", "4. Cache Statistics After Warming")
    
    # 5. Show performance metrics
    run_command("uv run frb-sec-analyzer cache performance", "5. Cache Performance Analytics")
    
    # 6. Test cache hits by accessing same data
    console.print("\n[bold]6. Testing Cache Hits[/bold]")
    console.print("Accessing previously cached data to demonstrate cache hits...")
    
    run_command("uv run frb-sec-analyzer filings JPM --limit 3")
    time.sleep(1)
    run_command("uv run frb-sec-analyzer filings BAC --limit 3")
    
    # 7. Show improved performance metrics
    run_command("uv run frb-sec-analyzer cache performance", "7. Performance After Cache Hits")
    
    # 8. Show final cache statistics
    run_command("uv run frb-sec-analyzer cache stats", "8. Final Cache Statistics")
    
    # 9. Demonstrate cache management
    console.print("\n[bold]9. Cache Management Options[/bold]")
    console.print("Available cache management commands:")
    
    table = Table()
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    
    table.add_row("cache stats", "Show cache size and entry counts")
    table.add_row("cache performance", "Show hit rates and response times")
    table.add_row("cache warm <tickers>", "Pre-load data for specified companies")
    table.add_row("cache cleanup", "Remove expired cache entries")
    table.add_row("cache clear", "Clear all cache data")
    table.add_row("cache clear <table>", "Clear specific cache table")
    
    console.print(table)
    
    console.print(Panel(
        "[bold green]Cache Demo Complete![/bold green]\n\n"
        "[bold]Key Benefits Demonstrated:[/bold]\n"
        "• [green]Faster Response Times[/green] - Cached data loads instantly\n"
        "• [green]Reduced API Calls[/green] - Respects SEC rate limits\n"
        "• [green]Compressed Storage[/green] - Efficient disk usage\n"
        "• [green]Performance Tracking[/green] - Monitor cache effectiveness\n"
        "• [green]Automatic Management[/green] - Size limits and cleanup\n\n"
        "[bold]Production Benefits:[/bold]\n"
        "• Analyze the same companies repeatedly without re-downloading\n"
        "• Warm cache during off-hours for faster analysis during business hours\n"
        "• Track cache performance to optimize analysis workflows\n"
        "• Automatic compression saves storage space\n"
        "• Built-in cache size management prevents disk space issues",
        title="Demo Summary"
    ))

if __name__ == "__main__":
    main()