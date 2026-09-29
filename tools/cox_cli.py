"""Compatibility entry point; the installed CLI uses cox_protocol."""

from cox_protocol.cox_cli import app

if __name__ == "__main__":
    app()
