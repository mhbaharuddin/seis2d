$ErrorActionPreference = 'Stop'
Write-Host "Creating virtual environment..."
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Write-Host "Installing dependencies..."
pip install -r requirements.txt
Write-Host "Done. Run with: python main.py"
