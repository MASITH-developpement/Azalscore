#
# Azalscore - Launcher pour Windows
# Ce script installe, met à jour et lance Azalscore
#

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "update", "logs", "status", "install", "diagnose", "help")]
    [string]$Action = "start"
)

# Configuration
$RepoUrl = "https://github.com/MASITH-developpement/Azalscore.git"
$Branch = "main"
$InstallDir = "$env:USERPROFILE\Azalscore"
$LogDir = "$env:USERPROFILE\.azalscore"
$LogFile = "$LogDir\launcher.log"

# Créer le dossier de logs
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# ═══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $Message -ForegroundColor $Color
    Add-Content -Path $LogFile -Value $logMessage
}

function Write-Info { Write-Log "[INFO] $args" "Cyan" }
function Write-Success { Write-Log "[✓] $args" "Green" }
function Write-Warning { Write-Log "[⚠] $args" "Yellow" }
function Write-Error { Write-Log "[✗] $args" "Red" }

function Test-Command {
    param([string]$Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Show-Logo {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                               ║" -ForegroundColor Cyan
    Write-Host "║     █████╗ ███████╗ █████╗ ██╗     ███████╗ ██████╗ ██████╗   ║" -ForegroundColor Cyan
    Write-Host "║    ██╔══██╗╚══███╔╝██╔══██╗██║     ██╔════╝██╔════╝██╔═══██╗  ║" -ForegroundColor Cyan
    Write-Host "║    ███████║  ███╔╝ ███████║██║     ███████╗██║     ██║   ██║  ║" -ForegroundColor Cyan
    Write-Host "║    ██╔══██║ ███╔╝  ██╔══██║██║     ╚════██║██║     ██║   ██║  ║" -ForegroundColor Cyan
    Write-Host "║    ██║  ██║███████╗██║  ██║███████╗███████║╚██████╗╚██████╔╝  ║" -ForegroundColor Cyan
    Write-Host "║    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚═════╝   ║" -ForegroundColor Cyan
    Write-Host "║                                                               ║" -ForegroundColor Cyan
    Write-Host "║                   Launcher Windows                            ║" -ForegroundColor Cyan
    Write-Host "║                                                               ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════
# DIAGNOSTIC SYSTÈME
# ═══════════════════════════════════════════════════════════════

function Get-SystemInfo {
    $osInfo = Get-CimInstance Win32_OperatingSystem
    $cpuInfo = Get-CimInstance Win32_Processor
    $ramGB = [math]::Round($osInfo.TotalVisibleMemorySize / 1MB, 1)
    $diskFree = [math]::Round((Get-PSDrive C).Free / 1GB, 1)

    return @{
        OSName = $osInfo.Caption
        OSVersion = $osInfo.Version
        OSBuild = $osInfo.BuildNumber
        Architecture = $env:PROCESSOR_ARCHITECTURE
        CPU = $cpuInfo.Name
        RAM = "${ramGB} GB"
        DiskFree = "${diskFree} GB"
    }
}

function Show-SystemDiagnose {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "                 DIAGNOSTIC SYSTÈME                            " -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""

    $sysInfo = Get-SystemInfo

    Write-Host "Système:" -ForegroundColor Magenta
    Write-Host "  OS:           $($sysInfo.OSName)" -ForegroundColor Green
    Write-Host "  Version:      $($sysInfo.OSVersion) (Build $($sysInfo.OSBuild))" -ForegroundColor Green
    Write-Host "  Architecture: $($sysInfo.Architecture)" -ForegroundColor Green
    Write-Host "  CPU:          $($sysInfo.CPU)" -ForegroundColor Green
    Write-Host "  RAM:          $($sysInfo.RAM)" -ForegroundColor Green
    Write-Host "  Disque libre: $($sysInfo.DiskFree)" -ForegroundColor Green
    Write-Host ""

    Write-Host "Logiciels:" -ForegroundColor Magenta

    # Git
    if (Test-Command "git") {
        $gitVersion = (git --version) -replace "git version ", ""
        Write-Host "  Git:          ✓ $gitVersion" -ForegroundColor Green
    } else {
        Write-Host "  Git:          ✗ Non installé" -ForegroundColor Red
    }

    # Docker
    if (Test-Command "docker") {
        $dockerVersion = (docker --version) -replace "Docker version ", "" -replace ",.*", ""
        Write-Host "  Docker:       ✓ $dockerVersion" -ForegroundColor Green

        # Docker en cours d'exécution?
        try {
            docker info 2>$null | Out-Null
            Write-Host "  Docker:       ✓ En cours d'exécution" -ForegroundColor Green
        } catch {
            Write-Host "  Docker:       ⚠ Installé mais arrêté" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Docker:       ✗ Non installé" -ForegroundColor Red
    }

    # Docker Compose
    try {
        docker compose version 2>$null | Out-Null
        Write-Host "  Compose:      ✓ Disponible" -ForegroundColor Green
    } catch {
        Write-Host "  Compose:      ✗ Non disponible" -ForegroundColor Red
    }

    # Node.js
    if (Test-Command "node") {
        $nodeVersion = node -v
        Write-Host "  Node.js:      ✓ $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "  Node.js:      ⚠ Non installé (optionnel)" -ForegroundColor Yellow
    }

    # WSL
    try {
        wsl --status 2>$null | Out-Null
        Write-Host "  WSL:          ✓ Disponible" -ForegroundColor Green
    } catch {
        Write-Host "  WSL:          ⚠ Non installé" -ForegroundColor Yellow
    }

    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════
# INSTALLATION DES PRÉREQUIS
# ═══════════════════════════════════════════════════════════════

function Install-Prerequisites {
    Write-Info "Vérification et installation des prérequis..."

    $missing = @()

    # Vérifier Git
    if (Test-Command "git") {
        Write-Success "Git est installé"
    } else {
        $missing += "git"
    }

    # Vérifier Docker
    if (Test-Command "docker") {
        Write-Success "Docker est installé"
    } else {
        $missing += "docker"
    }

    if ($missing.Count -eq 0) {
        Write-Success "Tous les prérequis sont installés"
        return $true
    }

    Write-Warning "Prérequis manquants: $($missing -join ', ')"

    # Vérifier si winget est disponible
    if (Test-Command "winget") {
        Write-Info "Installation via winget..."

        foreach ($package in $missing) {
            switch ($package) {
                "git" {
                    Write-Info "Installation de Git..."
                    winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements
                }
                "docker" {
                    Write-Info "Installation de Docker Desktop..."
                    winget install --id Docker.DockerDesktop -e --silent --accept-package-agreements --accept-source-agreements
                    Write-Warning "Redémarrage nécessaire après l'installation de Docker"
                }
            }
        }
    }
    # Sinon essayer Chocolatey
    elseif (Test-Command "choco") {
        Write-Info "Installation via Chocolatey..."

        foreach ($package in $missing) {
            switch ($package) {
                "git" {
                    Write-Info "Installation de Git..."
                    choco install git -y
                }
                "docker" {
                    Write-Info "Installation de Docker Desktop..."
                    choco install docker-desktop -y
                    Write-Warning "Redémarrage nécessaire après l'installation de Docker"
                }
            }
        }
    }
    else {
        Write-Warning "Aucun gestionnaire de paquets trouvé (winget ou chocolatey)"
        Write-Host ""
        Write-Host "Veuillez installer manuellement:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Git:    https://git-scm.com/download/win" -ForegroundColor Cyan
        Write-Host "  Docker: https://www.docker.com/products/docker-desktop/" -ForegroundColor Cyan
        Write-Host ""
        return $false
    }

    # Rafraîchir le PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    return $true
}

# ═══════════════════════════════════════════════════════════════
# GESTION DU DÉPÔT
# ═══════════════════════════════════════════════════════════════

function Update-Repository {
    Write-Info "Mise à jour depuis GitHub (branche $Branch)..."

    if (Test-Path "$InstallDir\.git") {
        Write-Info "Dépôt existant, mise à jour..."
        Push-Location $InstallDir

        # Sauvegarder les modifications
        $changes = git status --porcelain
        if ($changes) {
            Write-Warning "Modifications locales détectées, sauvegarde..."
            git stash push -m "Sauvegarde auto $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        }

        git fetch origin $Branch
        git checkout $Branch 2>$null
        git reset --hard origin/$Branch

        Pop-Location
        Write-Success "Dépôt mis à jour"
    }
    else {
        Write-Info "Premier lancement, clonage du dépôt..."

        if (Test-Path $InstallDir) {
            Remove-Item -Path $InstallDir -Recurse -Force
        }

        git clone -b $Branch $RepoUrl $InstallDir

        Write-Success "Dépôt cloné"
    }
}

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

function Setup-Environment {
    Write-Info "Configuration de l'environnement..."
    Push-Location $InstallDir

    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Write-Info "Création du fichier .env..."
            Copy-Item ".env.example" ".env"

            # Générer des clés sécurisées
            $secretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
            $bootstrapSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
            $dbPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

            # Remplacer les valeurs
            $content = Get-Content ".env" -Raw
            $content = $content -replace "CHANGEME_PASSWORD", $dbPassword
            $content = $content -replace "CHANGEME_SECRET_KEY", $secretKey
            $content = $content -replace "CHANGEME_BOOTSTRAP_SECRET", $bootstrapSecret
            Set-Content ".env" $content

            Write-Success "Fichier .env créé avec des clés sécurisées"
        }
    }
    else {
        Write-Success "Fichier .env existant conservé"
    }

    Pop-Location
}

# ═══════════════════════════════════════════════════════════════
# GESTION DE L'APPLICATION
# ═══════════════════════════════════════════════════════════════

function Start-DockerDesktop {
    Write-Info "Vérification de Docker..."

    try {
        docker info 2>$null | Out-Null
        Write-Success "Docker est en cours d'exécution"
        return $true
    }
    catch {
        Write-Warning "Docker n'est pas démarré. Tentative de lancement..."

        # Lancer Docker Desktop
        $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dockerPath) {
            Start-Process $dockerPath
        }

        Write-Info "Attente du démarrage de Docker (90s max)..."
        $counter = 0
        while ($counter -lt 90) {
            Start-Sleep -Seconds 3
            $counter += 3
            Write-Host "." -NoNewline

            try {
                docker info 2>$null | Out-Null
                Write-Host ""
                Write-Success "Docker est prêt!"
                return $true
            }
            catch {}
        }

        Write-Host ""
        Write-Error "Docker n'a pas démarré. Lancez-le manuellement."
        return $false
    }
}

function Start-Application {
    Write-Info "Démarrage d'Azalscore..."
    Push-Location $InstallDir

    # Arrêter les conteneurs existants
    Write-Info "Arrêt des conteneurs existants..."
    docker compose down 2>$null

    # Démarrer
    Write-Info "Construction et démarrage..."
    docker compose up --build -d

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Conteneurs démarrés"
    }
    else {
        Write-Error "Erreur lors du démarrage"
        Pop-Location
        return
    }

    # Attendre l'API
    Write-Info "Attente de l'API (60s max)..."
    $counter = 0
    while ($counter -lt 60) {
        Start-Sleep -Seconds 2
        $counter += 2
        Write-Host "." -NoNewline

        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                Write-Host ""
                Write-Success "API prête!"
                break
            }
        }
        catch {}
    }

    if ($counter -ge 60) {
        Write-Host ""
        Write-Warning "L'API n'est pas encore prête. Vérifiez: docker compose logs -f"
    }

    Pop-Location
}

function Stop-Application {
    Write-Info "Arrêt d'Azalscore..."
    if (Test-Path $InstallDir) {
        Push-Location $InstallDir
        docker compose down 2>$null
        Pop-Location
    }
    Write-Success "Application arrêtée"
}

function Show-ApplicationInfo {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "          Azalscore est en cours d'exécution!                  " -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "URLs d'accès:" -ForegroundColor Cyan
    Write-Host "  API Backend:     http://localhost:8000" -ForegroundColor White
    Write-Host "  Documentation:   http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  Health Check:    http://localhost:8000/health" -ForegroundColor White
    Write-Host ""
    Write-Host "Commandes utiles:" -ForegroundColor Cyan
    Write-Host "  Logs:      cd $InstallDir; docker compose logs -f" -ForegroundColor White
    Write-Host "  Arrêter:   .\azalscore.ps1 stop" -ForegroundColor White
    Write-Host "  Restart:   .\azalscore.ps1 restart" -ForegroundColor White
    Write-Host ""
}

function Show-Help {
    Write-Host ""
    Write-Host "Usage: .\azalscore.ps1 [COMMANDE]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Commandes:"
    Write-Host "  start       Démarrer Azalscore (par défaut)"
    Write-Host "  stop        Arrêter Azalscore"
    Write-Host "  restart     Redémarrer Azalscore"
    Write-Host "  update      Mettre à jour depuis GitHub"
    Write-Host "  logs        Afficher les logs"
    Write-Host "  status      État des conteneurs"
    Write-Host "  install     Installer les prérequis"
    Write-Host "  diagnose    Diagnostic du système"
    Write-Host "  help        Afficher cette aide"
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

switch ($Action) {
    "start" {
        Show-Logo
        Show-SystemDiagnose
        if (-not (Install-Prerequisites)) { exit 1 }
        if (-not (Start-DockerDesktop)) { exit 1 }
        Update-Repository
        Setup-Environment
        Start-Application
        Show-ApplicationInfo
    }
    "stop" {
        Stop-Application
    }
    "restart" {
        Stop-Application
        Start-Sleep -Seconds 2
        if (-not (Start-DockerDesktop)) { exit 1 }
        Start-Application
        Show-ApplicationInfo
    }
    "update" {
        if (-not (Install-Prerequisites)) { exit 1 }
        Update-Repository
        Write-Success "Mise à jour terminée. Utilisez 'restart' pour appliquer."
    }
    "logs" {
        if (Test-Path $InstallDir) {
            Push-Location $InstallDir
            docker compose logs -f
            Pop-Location
        }
    }
    "status" {
        if (Test-Path $InstallDir) {
            Push-Location $InstallDir
            docker compose ps
            Pop-Location
        }
    }
    "install" {
        Show-Logo
        Show-SystemDiagnose
        Install-Prerequisites
    }
    "diagnose" {
        Show-Logo
        Show-SystemDiagnose
    }
    "help" {
        Show-Logo
        Show-Help
    }
}
