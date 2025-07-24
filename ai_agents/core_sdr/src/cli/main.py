#!/usr/bin/env python3
"""
Lead Generation CLI Tool

Usage:
    python -m core_sdr cli search "AI startups in SF with 10+ employees"
    python -m core_sdr cli search --query "SaaS companies in NYC" --format csv --max-results 50
    python -m core_sdr cli explain "Public companies using AWS"
    python -m core_sdr cli health
"""
import json
import logging
import os
import sys
import asyncio
import click
from click import Context
from dotenv import load_dotenv

from ..core import LeadGenerationOrchestrator, LeadGenerationError

# Load environment variables
load_dotenv()


@click.group()
@click.option('--config-dir', default='config', help='Configuration directory')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx: Context, config_dir, verbose):
    """Lead Generation CLI Tool"""
    ctx.ensure_object(dict)
    
    # Set up logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get API configuration
    api_key = os.getenv('CORESIGNAL_API_KEY')
    if not api_key:
        click.echo("Error: CORESIGNAL_API_KEY environment variable not set", err=True)
        click.echo("Please set your CoreSignal API key in the .env file", err=True)
        sys.exit(1)
    
    base_url = os.getenv('CORESIGNAL_BASE_URL', 'https://api.coresignal.com')
    mongo_uri = os.getenv('MONGODB_URI')
    cache_ttl_hours = int(os.getenv('CACHE_TTL_HOURS', '24'))
    
    # Initialize orchestrator
    try:
        orchestrator = LeadGenerationOrchestrator(
            coresignal_api_key=api_key,
            coresignal_base_url=base_url,
            config_dir=config_dir,
            mongo_uri=mongo_uri,
            cache_ttl_hours=cache_ttl_hours
        )
        ctx.obj['orchestrator'] = orchestrator
    except Exception as e:
        click.echo(f"Error initializing system: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('query', required=False)
@click.option('--query', '-q', help='Search query (alternative to positional argument)')
@click.option('--format', '-f', 'output_format', 
              type=click.Choice(['json', 'csv', 'summary']), 
              default='summary', 
              help='Output format')
@click.option('--max-results', '-n', type=int, default=20, 
              help='Maximum number of results (1-100)')
@click.option('--timeout', '-t', type=int, default=30, 
              help='Request timeout in seconds (5-300)')
@click.option('--output', '-o', type=click.Path(), 
              help='Output file (default: stdout)')
@click.option('--interactive', '-i', is_flag=True, 
              help='Interactive mode - prompt for query')
@click.pass_context
def search(ctx, query, output_format, max_results, timeout, output, interactive):
    """Search for companies using natural language query."""
    orchestrator = ctx.obj['orchestrator']
    
    # Get query from user if not provided
    if interactive or not query:
        query = click.prompt('Enter your search query', type=str)
    
    if not query:
        click.echo("Error: Query is required", err=True)
        return
    
    # Prepare request data
    request_data = {
        'query': query,
        'max_results': max_results,
        'timeout': timeout,
        'output_format': output_format
    }
    
    try:
        # Process search request
        with click.progressbar(length=1, label='Searching companies...') as bar:
            response = asyncio.run(orchestrator.process_search_request(request_data))
            bar.update(1)
        
        # Format response
        formatted_output = orchestrator.format_response(response, output_format)
        
        # Output results
        if output:
            with open(output, 'w') as f:
                f.write(formatted_output)
            click.echo(f"Results saved to {output}")
        else:
            click.echo(formatted_output)
        
        # Show summary stats
        if output_format != 'summary':
            metadata = response.metadata
            click.echo(f"\nSummary: {response.results['returned']} companies found "
                      f"(Credits: {metadata['credits_used']}, "
                      f"Time: {metadata['processing_time']:.1f}s)", err=True)
        
    except LeadGenerationError as e:
        click.echo(f"Search error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


# explain command removed - Agent SDK handles query parsing automatically

@cli.command()
@click.pass_context
def health(ctx):
    """Check system health status."""
    orchestrator = ctx.obj['orchestrator']
    
    try:
        health_status = orchestrator.health_check()
        
        status_color = 'green' if health_status['status'] == 'healthy' else 'red'
        click.echo(f"System Status: ", nl=False)
        click.secho(health_status['status'].upper(), fg=status_color)
        
        click.echo("\nComponent Status:")
        for component, status in health_status['components'].items():
            color = 'green' if status == 'healthy' or status == 'configured' else 'red'
            click.echo(f"  {component}: ", nl=False)
            click.secho(status, fg=color)
        
    except Exception as e:
        click.echo(f"Health check error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show processing statistics."""
    orchestrator = ctx.obj['orchestrator']
    
    try:
        stats = orchestrator.get_stats()
        
        click.echo("Processing Statistics:")
        click.echo(f"  Total searches: {stats['total_searches']}")
        click.echo(f"  Cache hits: {stats['cache_hits']}")
        click.echo(f"  Cache misses: {stats['cache_misses']}")
        
        if stats['total_searches'] > 0:
            cache_rate = (stats['cache_hits'] / stats['total_searches']) * 100
            click.echo(f"  Cache hit rate: {cache_rate:.1f}%")
        
        click.echo(f"  Total tokens used: {stats['total_tokens_used']}")
        click.echo(f"  Total processing time: {stats['total_processing_time']:.1f}s")
        
        if 'api_usage' in stats:
            api_usage = stats['api_usage']
            click.echo(f"\nAgent SDK + MCP Usage:")
            if 'requests_made' in api_usage:
                click.echo(f"  Requests made: {api_usage['requests_made']}")
            if 'tokens_used' in api_usage:
                click.echo(f"  Tokens consumed: {api_usage['tokens_used']}")
            elif 'credits_used' in api_usage:
                click.echo(f"  Legacy credits: {api_usage['credits_used']} (from cache/fallback)")
        
    except Exception as e:
        click.echo(f"Stats error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def clear_cache(ctx, confirm):
    """Clear all cached data."""
    orchestrator = ctx.obj['orchestrator']
    
    if not confirm:
        click.confirm('Are you sure you want to clear all cached data?', abort=True)
    
    try:
        success = orchestrator.clear_cache()
        if success:
            click.echo("Cache cleared successfully")
        else:
            click.echo("Failed to clear cache", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"Cache clear error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
@click.pass_context
def demo(ctx, interactive):
    """Run demo searches to test the system."""
    orchestrator = ctx.obj['orchestrator']
    
    demo_queries = [
        "AI startups in San Francisco with 10+ employees",
        "Public SaaS companies in California using AWS",
        "Healthcare companies founded after 2020",
        "Fintech companies in NYC with 100+ employees"
    ]
    
    click.echo("Running demo searches...")
    
    for i, query in enumerate(demo_queries, 1):
        click.echo(f"\n{i}. Testing: {query}")
        
        if interactive:
            click.confirm('Run this search?', abort=True)
        
        try:
            request_data = {
                'query': query,
                'max_results': 5,
                'timeout': 30,
                'output_format': 'summary'
            }
            
            response = orchestrator.process_search_request(request_data)
            formatted_output = orchestrator.format_response(response, 'summary')
            
            # Show just the first few lines
            lines = formatted_output.split('\n')
            for line in lines[:8]:  # Show first 8 lines
                click.echo(f"   {line}")
            
            if len(lines) > 8:
                click.echo("   ...")
            
            metadata = response.metadata
            click.echo(f"   Results: {response.results['returned']} companies "
                      f"(Credits: {metadata['credits_used']}, "
                      f"Time: {metadata['processing_time']:.1f}s)")
        
        except Exception as e:
            click.echo(f"   Error: {str(e)}", err=True)
    
    click.echo("\nDemo completed!")


if __name__ == '__main__':
    cli()