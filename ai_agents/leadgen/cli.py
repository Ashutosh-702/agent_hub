"""
Lead Generation CLI Tool - Combines core_sdr and ai_sdr functionality.

Usage:
    leadgen dsl "give 1 company in Mumbai"          # Basic search
    leadgen dsl --company-employee "give 1 company in Mumbai"   # Full search with employees
"""

import os
import sys
import asyncclick as click
from click import Context
from dotenv import load_dotenv

from ai_agents.leadgen.workflow.search import run_basic_workflow, run_full_workflow

load_dotenv()


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx: Context, verbose):
    """Lead Generation CLI Tool"""
    ctx.ensure_object(dict)


@cli.command()
@click.argument('query', required=False)
@click.option('--company', 'mode', flag_value='company', default=True, help='Only search for companies (default)')
@click.option('--company-employee', 'mode', flag_value='company-employee', help='Search for companies and their employees')
@click.pass_context
async def dsl(ctx, query, mode):
    """Generate Elasticsearch DSL query from natural language."""
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        click.echo("Error: OPENAI_API_KEY environment variable not set", err=True)
        sys.exit(1)
    if not query:
        click.echo("Error: Query is required for DSL generation", err=True)
        return

    try:
        if mode == 'company':
            click.echo(f"Running company search for: {query}")
            results = await run_basic_workflow(query)
            click.echo(f"Basic results: {results}")

        else:
            click.echo(f"Running company and employee search for: {query}")
            results = await run_full_workflow(query)

            click.echo(f"Full results: {results}")

    except Exception as e:
        click.echo(f"Processing error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()