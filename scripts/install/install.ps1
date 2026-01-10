#Requires -Version 7.0
#Requires -RunAsAdministrator
<#
.SYNOPSIS
    AZALSCORE - Script d'installation Windows

.DESCRIPTION
    Script d'installation automatisée pour AZALSCORE sur Windows.
    Installe Python, PostgreSQL (optionnel), configure l'environnement virtuel
    et génère les secrets de manière sécurisée.

.PARAMETER Mode
    Mode d'installation: dev (défaut), prod, ou cloud

.PARAMETER NonInteractive
    Exécution sans prompts interactifs

.PARAMETER SkipPostgres
    Ne pas installer PostgreSQL (utiliser une instance existante)

.EXAMPLE
    .\install.ps1
    Installation interactive en mode développement

.EXAMPLE
    .\install.ps1 -Mode prod -NonInteractive
    Installation production sans interaction

.NOTES
    Auteur: AZALS DevOps Team
    Version: 1.0.0
    Requiert: PowerShell 7+, Droits administrateur
#>

[CmdletBinding()]
param(
    [ValidateSet('dev', 'prod', 'cloud')]
    [string]$Mode = 'dev',

    [switch]$NonInteractive,

    [switch]$SkipPostgres,

    [switch]$DryRun
)

#===============================================================================
# CONFIGURATION
#===============================================================================

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$Script:Version = '1.0.0'
$Script:ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Script:LogFile = Join-Path $Script:ProjectRoot 'install.log'
$Script:MinPythonVersion = [Version]'3.11'
$Script:PostgresVersion = '15'

# Secrets générés
$Script:GeneratedSecrets = @{}

#===============================================================================
# FONCTIONS UTILITAIRES
#===============================================================================

function Write-Log {
    param(
        [ValidateSet('INFO', 'OK', 'WARN', 'ERROR', 'DEBUG')]
        [string]$Level,
        [string]$Message
    )

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $colors = @{
        'INFO'  = 'Cyan'
        'OK'    = 'Green'
        'WARN'  = 'Yellow'
        'ERROR' = 'Red'
        'DEBUG' = 'Gray'
    }

    $prefix = switch ($Level) {
        'INFO'  { '[INFO]' }
        'OK'    { '[OK]' }
        'WARN'  { '[WARN]' }
        'ERROR' { '[ERROR]' }
        'DEBUG' { '[DEBUG]' }
    }

    Write-Host "$prefix " -ForegroundColor $colors[$Level] -NoNewline
    Write-Host $Message

    # Log to file
    Add-Content -Path $Script:LogFile -Value "[$timestamp] [$Level] $Message"
}

function Show-Banner {
    $banner = @"

    ___   _____   _   _     _____  _____ _____ _____ _____
   / _ \ |__  /  / \ | |   /  ___|/  __ \  _  | ___ \  ___|
  / /_\ \  / /  / _ \| |   \ ``--. | /  \/ | | | |_/ / |__
  |  _  | / /  / ___ \ |    ``--. \| |   | | | |    /|  __|
  |_| |_|/_/  /_/   \_\_|___/\__/ | \__/\ \_/ / |\ \| |___
                       \_____\____/ \____/\___/\_| \_\____/

"@

    Write-Host $banner -ForegroundColor Cyan
    Write-Host "AZALSCORE - Installation Windows v$($Script:Version)" -ForegroundColor White
    Write-Host ("=" * 78) -ForegroundColor Cyan
    Write-Host ""
}

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-UserConfirmation {
    param([string]$Message, [bool]$Default = $true)

    if ($NonInteractive) {
        return $Default
    }

    $defaultText = if ($Default) { "[Y/n]" } else { "[y/N]" }
    $response = Read-Host "$Message $defaultText"

    if ([string]::IsNullOrWhiteSpace($response)) {
        return $Default
    }

    return $response -match '^[Yy]'
}

#===============================================================================
# VÉRIFICATIONS SYSTÈME
#===============================================================================

function Test-SystemRequirements {
    Write-Log INFO "Vérification des prérequis système..."

    # Vérifier PowerShell version
    if ($PSVersionTable.PSVersion.Major -lt 7) {
        Write-Log ERROR "PowerShell 7+ requis (version actuelle: $($PSVersionTable.PSVersion))"
        Write-Log INFO "Téléchargez PowerShell 7: https://github.com/PowerShell/PowerShell/releases"
        exit 1
    }
    Write-Log OK "PowerShell $($PSVersionTable.PSVersion)"

    # Vérifier les droits admin
    if (-not (Test-Administrator)) {
        Write-Log ERROR "Droits administrateur requis"
        Write-Log INFO "Relancez PowerShell en tant qu'administrateur"
        exit 1
    }
    Write-Log OK "Droits administrateur"

    # Vérifier l'espace disque
    $drive = (Get-Item $Script:ProjectRoot).PSDrive
    $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
    if ($freeSpaceGB -lt 2) {
        Write-Log WARN "Espace disque faible: ${freeSpaceGB}GB (2GB+ recommandé)"
    } else {
        Write-Log OK "Espace disque: ${freeSpaceGB}GB"
    }

    # Vérifier la connexion Internet
    try {
        $null = Invoke-WebRequest -Uri 'https://pypi.org' -Method Head -TimeoutSec 5
        Write-Log OK "Connexion Internet"
    } catch {
        Write-Log ERROR "Pas de connexion Internet"
        exit 1
    }

    # Vérifier les ports
    $portsToCheck = @(
        @{ Port = 8000; Name = "API AZALSCORE" },
        @{ Port = 5432; Name = "PostgreSQL" }
    )

    foreach ($portInfo in $portsToCheck) {
        $listener = Get-NetTCPConnection -LocalPort $portInfo.Port -State Listen -ErrorAction SilentlyContinue
        if ($listener) {
            Write-Log WARN "Port $($portInfo.Port) ($($portInfo.Name)) déjà utilisé"
        }
    }

    Write-Log OK "Vérifications système terminées"
}

#===============================================================================
# INSTALLATION PYTHON
#===============================================================================

function Install-Python {
    Write-Log INFO "Configuration de Python..."

    # Chercher Python existant
    $pythonCmd = $null
    $pythonVersion = $null

    foreach ($cmd in @('python', 'python3', 'py')) {
        try {
            $versionOutput = & $cmd --version 2>&1
            if ($versionOutput -match 'Python (\d+\.\d+)') {
                $version = [Version]$Matches[1]
                if ($version -ge $Script:MinPythonVersion) {
                    $pythonCmd = $cmd
                    $pythonVersion = $version
                    break
                }
            }
        } catch {
            continue
        }
    }

    if ($null -eq $pythonCmd) {
        Write-Log INFO "Python $($Script:MinPythonVersion)+ non trouvé, installation..."

        # Installer via winget si disponible
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-Log INFO "Installation via winget..."
            winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements

            # Rafraîchir le PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("Path", "User")

            $pythonCmd = 'python'
        } else {
            Write-Log INFO "Installation via Chocolatey..."

            # Installer Chocolatey si nécessaire
            if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
                Set-ExecutionPolicy Bypass -Scope Process -Force
                [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
                Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            }

            choco install python312 -y
            $pythonCmd = 'python'
        }

        # Vérifier l'installation
        try {
            $versionOutput = & python --version 2>&1
            if ($versionOutput -match 'Python (\d+\.\d+)') {
                $pythonVersion = [Version]$Matches[1]
            }
        } catch {
            Write-Log ERROR "Échec de l'installation de Python"
            exit 1
        }
    }

    Write-Log OK "Python $pythonVersion ($pythonCmd)"

    # Stocker pour utilisation ultérieure
    $Script:PythonCmd = $pythonCmd
    $Script:PythonVersion = $pythonVersion
}

function New-VirtualEnvironment {
    Write-Log INFO "Création de l'environnement virtuel..."

    $venvPath = Join-Path $Script:ProjectRoot 'venv'

    # Supprimer l'ancien venv si existant
    if (Test-Path $venvPath) {
        if (Get-UserConfirmation "Environnement virtuel existant. Le recréer?") {
            Remove-Item -Recurse -Force $venvPath
        } else {
            Write-Log INFO "Conservation de l'environnement existant"
            return
        }
    }

    # Créer le venv
    & $Script:PythonCmd -m venv $venvPath

    if (-not (Test-Path $venvPath)) {
        Write-Log ERROR "Échec de la création du venv"
        exit 1
    }

    # Activer le venv
    $activateScript = Join-Path $venvPath 'Scripts\Activate.ps1'
    . $activateScript

    # Mettre à jour pip
    Write-Log INFO "Mise à jour de pip..."
    python -m pip install --upgrade pip setuptools wheel --quiet

    Write-Log OK "Environnement virtuel créé"
}

function Install-PythonDependencies {
    Write-Log INFO "Installation des dépendances Python..."

    $requirementsFile = Join-Path $Script:ProjectRoot 'requirements.txt'
    $requirementsDevFile = Join-Path $Script:ProjectRoot 'requirements-dev.txt'

    if (-not (Test-Path $requirementsFile)) {
        Write-Log ERROR "Fichier requirements.txt non trouvé"
        exit 1
    }

    pip install -r $requirementsFile --quiet

    if ($Mode -eq 'dev' -and (Test-Path $requirementsDevFile)) {
        Write-Log INFO "Installation des dépendances de développement..."
        pip install -r $requirementsDevFile --quiet
    }

    Write-Log OK "Dépendances installées"
}

#===============================================================================
# POSTGRESQL
#===============================================================================

function Install-PostgreSQL {
    if ($SkipPostgres) {
        Write-Log INFO "Installation PostgreSQL ignorée (--SkipPostgres)"
        return
    }

    Write-Log INFO "Configuration de PostgreSQL..."

    # Vérifier si PostgreSQL est déjà installé
    $pgService = Get-Service -Name 'postgresql*' -ErrorAction SilentlyContinue

    if ($pgService) {
        Write-Log INFO "PostgreSQL déjà installé"

        if ($pgService.Status -ne 'Running') {
            Start-Service $pgService.Name
        }
        Write-Log OK "PostgreSQL en cours d'exécution"
        return
    }

    if (-not (Get-UserConfirmation "Installer PostgreSQL localement?")) {
        Write-Log INFO "PostgreSQL sera configuré manuellement"
        $Script:SkipPostgres = $true
        return
    }

    Write-Log INFO "Installation de PostgreSQL $Script:PostgresVersion..."

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install PostgreSQL.PostgreSQL --silent --accept-package-agreements
    } elseif (Get-Command choco -ErrorAction SilentlyContinue) {
        choco install postgresql15 -y
    } else {
        Write-Log WARN "Veuillez installer PostgreSQL manuellement"
        Write-Log INFO "Téléchargement: https://www.postgresql.org/download/windows/"
        $Script:SkipPostgres = $true
        return
    }

    # Attendre le démarrage du service
    Start-Sleep -Seconds 5
    $pgService = Get-Service -Name 'postgresql*' -ErrorAction SilentlyContinue
    if ($pgService -and $pgService.Status -eq 'Running') {
        Write-Log OK "PostgreSQL installé et démarré"
    } else {
        Write-Log WARN "PostgreSQL installé mais le service n'est pas démarré"
    }
}

#===============================================================================
# GÉNÉRATION DES SECRETS
#===============================================================================

function New-SecureSecret {
    param([int]$Length = 32)

    $bytes = New-Object byte[] $Length
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::Create()
    $rng.GetBytes($bytes)
    return [Convert]::ToBase64String($bytes) -replace '[+/=]', '' | Select-Object -First ($Length * 2)
}

function New-HexSecret {
    param([int]$Length = 32)

    $bytes = New-Object byte[] $Length
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::Create()
    $rng.GetBytes($bytes)
    return [BitConverter]::ToString($bytes) -replace '-', '' | Select-Object -First ($Length * 2)
}

function New-FernetKey {
    # Génère une clé Fernet valide (32 bytes en base64)
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::Create()
    $rng.GetBytes($bytes)
    return [Convert]::ToBase64String($bytes)
}

function New-AllSecrets {
    Write-Log INFO "Génération des secrets cryptographiques..."

    $Script:GeneratedSecrets = @{
        'SECRET_KEY'        = New-HexSecret -Length 32
        'BOOTSTRAP_SECRET'  = New-HexSecret -Length 32
        'ENCRYPTION_KEY'    = New-FernetKey
        'POSTGRES_PASSWORD' = New-SecureSecret -Length 24
        'API_KEY'           = New-HexSecret -Length 24
    }

    if ($Mode -eq 'prod') {
        $Script:GeneratedSecrets['REDIS_PASSWORD'] = New-SecureSecret -Length 20
    }

    Write-Log OK "Secrets générés"

    # Afficher un résumé masqué
    Write-Host ""
    Write-Host "Secrets générés:" -ForegroundColor White
    Write-Host ("-" * 40)
    foreach ($key in $Script:GeneratedSecrets.Keys) {
        $value = $Script:GeneratedSecrets[$key]
        $masked = $value.Substring(0, 4) + "..." + $value.Substring($value.Length - 4)
        Write-Host "  ${key}: $masked"
    }
    Write-Host ("-" * 40)
    Write-Host ""
}

#===============================================================================
# FICHIER .ENV
#===============================================================================

function New-EnvFile {
    Write-Log INFO "Génération du fichier .env..."

    $envFile = Join-Path $Script:ProjectRoot '.env'
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

    $dbPassword = $Script:GeneratedSecrets['POSTGRES_PASSWORD']
    $secretKey = $Script:GeneratedSecrets['SECRET_KEY']
    $bootstrapSecret = $Script:GeneratedSecrets['BOOTSTRAP_SECRET']
    $encryptionKey = $Script:GeneratedSecrets['ENCRYPTION_KEY']

    # Backup de l'ancien .env
    if (Test-Path $envFile) {
        $backupFile = "$envFile.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $envFile $backupFile
        Write-Log INFO "Ancien .env sauvegardé: $backupFile"
    }

    if ($Mode -eq 'dev') {
        $envContent = @"
#===============================================================================
# AZALSCORE - Configuration Développement (Windows)
#===============================================================================
# Généré automatiquement le $timestamp
# NE PAS VERSIONNER CE FICHIER
#===============================================================================

# Environnement
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Base de données PostgreSQL
POSTGRES_DB=azals
POSTGRES_USER=azals_user
POSTGRES_PASSWORD=$dbPassword
DATABASE_URL=postgresql+psycopg2://azals_user:${dbPassword}@localhost:5432/azals

# Pool de connexions
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Sécurité
SECRET_KEY=$secretKey
BOOTSTRAP_SECRET=$bootstrapSecret

# UUID
DB_STRICT_UUID=true
DB_RESET_UUID=false
DB_AUTO_RESET_ON_VIOLATION=false

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
AUTH_RATE_LIMIT_PER_MINUTE=10

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# Version
VERSION=0.3.0
"@
    } else {
        $envContent = @"
#===============================================================================
# AZALSCORE - Configuration Production (Windows)
#===============================================================================
# Généré automatiquement le $timestamp
# NE JAMAIS VERSIONNER CE FICHIER
#===============================================================================

# Environnement
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Base de données PostgreSQL
POSTGRES_DB=azals
POSTGRES_USER=azals_user
POSTGRES_PASSWORD=$dbPassword
DATABASE_URL=postgresql+psycopg2://azals_user:${dbPassword}@localhost:5432/azals

# Pool de connexions
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Sécurité
SECRET_KEY=$secretKey
BOOTSTRAP_SECRET=$bootstrapSecret
ENCRYPTION_KEY=$encryptionKey

# UUID
DB_STRICT_UUID=true
DB_RESET_UUID=false
DB_AUTO_RESET_ON_VIOLATION=false

# CORS (REMPLACER PAR VOTRE DOMAINE)
CORS_ORIGINS=https://votre-domaine.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
AUTH_RATE_LIMIT_PER_MINUTE=5

# API
API_HOST=127.0.0.1
API_PORT=8000
API_WORKERS=4

# Version
VERSION=0.3.0
"@
    }

    Set-Content -Path $envFile -Value $envContent -Encoding UTF8

    Write-Log OK "Fichier .env généré"
}

#===============================================================================
# SCRIPTS DE DÉMARRAGE
#===============================================================================

function New-StartupScripts {
    Write-Log INFO "Création des scripts de démarrage..."

    # Script de démarrage développement
    $devScript = Join-Path $Script:ProjectRoot 'start_dev.ps1'
    $devContent = @'
#Requires -Version 7.0
# AZALSCORE - Démarrage Développement

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  AZALSCORE - Mode Développement" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Activer le venv
$venvActivate = Join-Path $ScriptDir 'venv\Scripts\Activate.ps1'
if (Test-Path $venvActivate) {
    . $venvActivate
} else {
    Write-Host "Environnement virtuel non trouvé!" -ForegroundColor Red
    exit 1
}

# Charger les variables d'environnement
$envFile = Join-Path $ScriptDir '.env'
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
        }
    }
}

# Variables de développement
$env:AZALS_ENV = 'dev'
$env:DEBUG = 'true'
$env:DB_STRICT_UUID = 'true'

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Environment: $env:ENVIRONMENT"
Write-Host "  Debug: $env:DEBUG"
Write-Host "  API: http://localhost:8000"
Write-Host "  Docs: http://localhost:8000/docs"
Write-Host ""

Set-Location $ScriptDir
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app
'@

    Set-Content -Path $devScript -Value $devContent -Encoding UTF8
    Write-Log OK "Script start_dev.ps1 créé"

    # Script de démarrage production
    $prodScript = Join-Path $Script:ProjectRoot 'start_prod.ps1'
    $prodContent = @'
#Requires -Version 7.0
# AZALSCORE - Démarrage Production

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "======================================" -ForegroundColor Green
Write-Host "  AZALSCORE - Mode Production" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Vérifications de sécurité
$envFile = Join-Path $ScriptDir '.env'
if (-not (Test-Path $envFile)) {
    Write-Host "ERREUR: Fichier .env non trouvé!" -ForegroundColor Red
    exit 1
}

$envContent = Get-Content $envFile -Raw
if ($envContent -match 'DEBUG=true') {
    Write-Host "ERREUR: DEBUG=true interdit en production!" -ForegroundColor Red
    exit 1
}

# Activer le venv
$venvActivate = Join-Path $ScriptDir 'venv\Scripts\Activate.ps1'
. $venvActivate

# Charger les variables d'environnement
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}

# Variables de production (forcées)
$env:AZALS_ENV = 'prod'
$env:DEBUG = 'false'
$env:DB_STRICT_UUID = 'true'
$env:DB_AUTO_RESET_ON_VIOLATION = 'false'
$env:DB_RESET_UUID = 'false'

$workers = $env:API_WORKERS
if (-not $workers) { $workers = [Environment]::ProcessorCount }

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Environment: production"
Write-Host "  Workers: $workers"
Write-Host ""

Set-Location $ScriptDir
gunicorn app.main:app `
    --worker-class uvicorn.workers.UvicornWorker `
    --workers $workers `
    --bind "127.0.0.1:8000" `
    --timeout 120
'@

    Set-Content -Path $prodScript -Value $prodContent -Encoding UTF8
    Write-Log OK "Script start_prod.ps1 créé"
}

#===============================================================================
# INSTALLATION AZALSCORE
#===============================================================================

function Install-Azalscore {
    Write-Log INFO "Installation de AZALSCORE..."

    # Charger les variables d'environnement
    $envFile = Join-Path $Script:ProjectRoot '.env'
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
        }
    }

    # Vérifier l'import de l'application
    Write-Log INFO "Vérification de l'application..."
    Set-Location $Script:ProjectRoot

    try {
        python -c "from app.main import app; print('Import OK')"
        Write-Log OK "Import de l'application réussi"
    } catch {
        Write-Log ERROR "Échec de l'import de l'application"
        Write-Log ERROR $_.Exception.Message
        exit 1
    }

    # Exécuter les migrations
    Write-Log INFO "Application des migrations..."
    try {
        alembic upgrade head
        Write-Log OK "Migrations appliquées"
    } catch {
        Write-Log WARN "Avertissements lors des migrations"
    }

    Write-Log OK "AZALSCORE installé"
}

#===============================================================================
# RÉSUMÉ FINAL
#===============================================================================

function Show-Summary {
    Write-Host ""
    Write-Host ("=" * 78) -ForegroundColor Cyan
    Write-Host "   AZALSCORE - Installation terminée" -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor Cyan
    Write-Host ""

    Write-Host "Installation:" -ForegroundColor White
    Write-Host ("-" * 40)
    Write-Host "  Mode:        $Mode"
    Write-Host "  Répertoire:  $Script:ProjectRoot"
    Write-Host "  Python:      $Script:PythonVersion"
    Write-Host ""

    Write-Host "Prochaines étapes:" -ForegroundColor White
    Write-Host ("-" * 40)

    if ($Mode -eq 'dev') {
        Write-Host ""
        Write-Host "  1. Démarrer l'application:" -ForegroundColor Yellow
        Write-Host "     .\start_dev.ps1" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  2. Accéder à l'interface:" -ForegroundColor Yellow
        Write-Host "     API:  http://localhost:8000"
        Write-Host "     Docs: http://localhost:8000/docs"
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "  1. Configurer PostgreSQL manuellement" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  2. Démarrer l'application:" -ForegroundColor Yellow
        Write-Host "     .\start_prod.ps1" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  3. Configurer un reverse proxy (IIS/Nginx)" -ForegroundColor Yellow
        Write-Host ""
    }

    Write-Host "Commandes utiles:" -ForegroundColor White
    Write-Host ("-" * 40)
    Write-Host "  # Activer l'environnement virtuel"
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  # Exécuter les migrations"
    Write-Host "  alembic upgrade head" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  # Lancer les tests"
    Write-Host "  pytest" -ForegroundColor Cyan
    Write-Host ""

    Write-Host ("=" * 78) -ForegroundColor Green
    Write-Host "   Installation réussie!" -ForegroundColor Green
    Write-Host ("=" * 78) -ForegroundColor Green
    Write-Host ""
}

#===============================================================================
# POINT D'ENTRÉE PRINCIPAL
#===============================================================================

function Main {
    # Initialiser le log
    $null = New-Item -ItemType File -Path $Script:LogFile -Force

    Show-Banner

    Write-Log INFO "Démarrage de l'installation en mode: $Mode"

    # Vérifications système
    Test-SystemRequirements

    # Installation Python
    Install-Python
    New-VirtualEnvironment
    Install-PythonDependencies

    # PostgreSQL
    Install-PostgreSQL

    # Génération des secrets
    New-AllSecrets

    # Fichier .env
    New-EnvFile

    # Scripts de démarrage
    New-StartupScripts

    # Installation AZALSCORE
    Install-Azalscore

    # Résumé
    Show-Summary
}

# Exécution
try {
    Main
} catch {
    Write-Log ERROR "Erreur fatale: $_"
    Write-Log ERROR $_.ScriptStackTrace
    exit 1
}
