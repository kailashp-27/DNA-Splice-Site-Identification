# Optional settings. Apply in PowerShell with: . .\config.example.ps1
# Normal launch needs no settings file; these are the tested defaults.
$env:ECOSPLICE_PORT = '8765'
$env:ECOSPLICE_DB_PATH = Join-Path $PSScriptRoot 'data/local/runs.sqlite3'
$env:ECOSPLICE_MODEL_DIR = Join-Path $PSScriptRoot 'models/ecosplice-v1'
