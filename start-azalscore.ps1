# ============================================================
# AZALSCORE - Script de démarrage automatique
# ============================================================
# Ce script:
# 1. Met à jour le code depuis la branche main
# 2. Démarre le backend (port 8001)
# 3. Démarre le frontend (port 3000)
# ============================================================

$ErrorActionPreference = "Continue"
$ProjectPath = $PSScriptRoot
if (-not $ProjectPath) {
    $ProjectPath = "C:\Users\masith\Documents\Azalscore"
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "        AZALSCORE - Demarrage automatique" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Se placer dans le répertoire du projet
Set-Location $ProjectPath
Write-Host "[1/5] Repertoire: $ProjectPath" -ForegroundColor Yellow

# Arrêter les anciens processus Python sur le port 8001
Write-Host "[2/5] Arret des anciens processus..." -ForegroundColor Yellow
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Mettre à jour depuis main
Write-Host "[3/5] Mise a jour depuis la branche main..." -ForegroundColor Yellow
git fetch origin main
git checkout main
git pull origin main

# Supprimer le cache Python
Write-Host "[4/5] Nettoyage du cache Python..." -ForegroundColor Yellow
Get-ChildItem -Path . -Include "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Démarrer le backend dans une nouvelle fenêtre
Write-Host "[5/5] Demarrage des serveurs..." -ForegroundColor Yellow
Write-Host ""

# Backend (nouvelle fenêtre PowerShell)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectPath'; Write-Host 'AZALSCORE Backend - Port 8001' -ForegroundColor Green; python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

# Attendre que le backend démarre
Write-Host "   Attente du backend (5 secondes)..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Frontend (nouvelle fenêtre PowerShell)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectPath\frontend'; Write-Host 'AZALSCORE Frontend - Port 3000' -ForegroundColor Green; npm run dev"

# Message final
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "        AZALSCORE demarre!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "   Backend:  http://localhost:8001" -ForegroundColor White
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "   Connexion: contact@masith.fr / Elisabette04@04!" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Appuyez sur une touche pour ouvrir le navigateur..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Ouvrir le navigateur
Start-Process "http://localhost:3000"
