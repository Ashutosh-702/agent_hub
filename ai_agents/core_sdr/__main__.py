#!/usr/bin/env python3
"""
Main entry point for the lead generation system.

This allows the package to be run as:
    python -m core_sdr
"""

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'api':
        # Start API server
        import uvicorn
        uvicorn.run(
            "core_sdr.src.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    else:
        # Default to CLI
        from .src.cli.main import cli
        
        # Remove 'api' from args if present to avoid conflicts
        if len(sys.argv) > 1 and sys.argv[1] == 'cli':
            sys.argv.pop(1)
        
        cli()