# Standalone CLI

This folder contains the CLI entry point for mart1 as a separate launch target.

## Run

From this folder, start the CLI with:

```bash
python cli.py
```

The CLI reuses the shared backend modules from the parent mart1 directory, but it is organized as its own folder so it stays separate from the FastAPI entrypoint.
