<#
.SYNOPSIS
    Script auxiliar para exportar jogos da biblioteca do Playnite para playnite_games.json.
.DESCRIPTION
    Lê o banco de dados do Playnite (games.db via LiteDB), mapeia plataformas/emuladores,
    e salva em playnite_games.json para integração total com o Choose Random Game.
#>

param (
    [string]$PlaynitePath = "E:\Util\Playnite",
    [string]$OutputFile = "$PSScriptRoot\playnite_games.json",
    [switch]$OnlyInstalled = $false,
    [switch]$AutoRestartIfLocked = $true
)

$dbPath = Join-Path $PlaynitePath "library\games.db"
$dllPath = Join-Path $PlaynitePath "LiteDB.dll"

if (-not (Test-Path $dbPath)) {
    Write-Warning "Banco de dados do Playnite não encontrado em: $dbPath"
    exit 1
}

if (-not (Test-Path $dllPath)) {
    Write-Warning "LiteDB.dll não encontrado em: $dllPath"
    exit 1
}

Add-Type -Path $dllPath

# Function to perform the export
function Do-Export {
    param([string]$targetDbPath)

    # 1. Carregar mapa de plataformas / emuladores
    $platformsMap = @{}
    $platformsDbPath = Join-Path $PlaynitePath "library\platforms.db"
    if (Test-Path $platformsDbPath) {
        try {
            $pDb = New-Object LiteDB.LiteDatabase("Filename=$platformsDbPath;ReadOnly=true")
            $pCol = $pDb.GetCollection("Platform")
            foreach ($p in $pCol.FindAll()) {
                if ($p["_id"] -and $p["Name"]) {
                    $platformsMap[$p["_id"].AsGuid.ToString()] = $p["Name"].AsString
                }
            }
            $pDb.Dispose()
        } catch {
            Write-Verbose "Não foi possível carregar platforms.db: $_"
        }
    }

    # 2. Carregar mapa de fontes (Steam, GOG, Epic, Xbox, Amazon, etc.)
    $sourcesMap = @{}
    $sourcesDbPath = Join-Path $PlaynitePath "library\sources.db"
    if (Test-Path $sourcesDbPath) {
        try {
            $sDb = New-Object LiteDB.LiteDatabase("Filename=$sourcesDbPath;ReadOnly=true")
            $sCol = $sDb.GetCollection("GameSource")
            foreach ($s in $sCol.FindAll()) {
                if ($s["_id"] -and $s["Name"]) {
                    $sourcesMap[$s["_id"].AsGuid.ToString()] = $s["Name"].AsString
                }
            }
            $sDb.Dispose()
        } catch {
            Write-Verbose "Não foi possível carregar sources.db: $_"
        }
    }

    # 3. Carregar catálogo completo de jogos
    $connStr = "Filename=$targetDbPath;ReadOnly=true"
    $db = New-Object LiteDB.LiteDatabase($connStr)
    $col = $db.GetCollection("Game")
    $allGames = $col.FindAll()

    $exportList = [System.Collections.Generic.List[PSCustomObject]]::new()
    foreach ($g in $allGames) {
        $isInstalled = [bool]$g["IsInstalled"].AsBoolean
        if ($OnlyInstalled -and (-not $isInstalled)) {
            continue
        }

        # Extrair plataforma / emulador
        $platNames = @()
        if ($g["PlatformIds"] -and $g["PlatformIds"].IsArray) {
            foreach ($platItem in $g["PlatformIds"].AsArray) {
                try {
                    $platGuid = $platItem.AsGuid.ToString()
                    if ($platformsMap.ContainsKey($platGuid)) {
                        $platNames += $platformsMap[$platGuid]
                    }
                } catch {}
            }
        }
        $platStr = if ($platNames.Count -gt 0) { $platNames -join ", " } else { "" }

        # Extrair fonte
        $srcName = "Playnite"
        if ($g["SourceId"]) {
            try {
                $srcGuid = $g["SourceId"].AsGuid.ToString()
                if ($sourcesMap.ContainsKey($srcGuid)) {
                    $srcName = $sourcesMap[$srcGuid]
                }
            } catch {}
        }

        $item = [PSCustomObject]@{
            Id = $g["_id"].AsString
            Name = $g["Name"].AsString
            IsInstalled = $isInstalled
            Platform = $platStr
            Source = $srcName
            Playtime = if ($g["Playtime"]) { $g["Playtime"].AsInt64 } else { 0 }
            PlayCount = if ($g["PlayCount"]) { $g["PlayCount"].AsInt32 } else { 0 }
            CoverImage = if ($g["CoverImage"]) { $g["CoverImage"].AsString } else { "" }
            Icon = if ($g["Icon"]) { $g["Icon"].AsString } else { "" }
        }
        $exportList.Add($item)
    }

    $db.Dispose()

    # Salvar JSON
    $json = $exportList | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText($OutputFile, $json, [System.Text.Encoding]::UTF8)
    Write-Host "Sucesso! Foram exportados $($exportList.Count) jogos para $OutputFile" -ForegroundColor Green
    return $exportList.Count
}

Write-Host "Carregando biblioteca completa do Playnite ($dbPath)..." -ForegroundColor Cyan

try {
    Do-Export -targetDbPath $dbPath
} catch {
    $err = $_.ToString()
    if ($err -match "outro processo|used by another process" -and $AutoRestartIfLocked) {
        Write-Warning "Playnite está aberto e bloqueando o banco de dados. Tentando exportação rápida..."
        $playniteProc = Get-Process Playnite.DesktopApp -ErrorAction SilentlyContinue
        if ($playniteProc) {
            Write-Host "Fechando Playnite graciosamente para ler banco de dados..." -ForegroundColor Yellow
            $playniteProc.CloseMainWindow() | Out-Null
            $closed = $playniteProc.WaitForExit(6000)
            if (-not $closed) {
                Stop-Process -Id $playniteProc.Id -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 800
            }

            try {
                Do-Export -targetDbPath $dbPath
            } finally {
                $appExe = Join-Path $PlaynitePath "Playnite.DesktopApp.exe"
                if (Test-Path $appExe) {
                    Write-Host "Reabrindo Playnite..." -ForegroundColor Cyan
                    Start-Process $appExe
                }
            }
        } else {
            Write-Error "Erro ao acessar banco de dados do Playnite: $_"
        }
    } else {
        Write-Error "Erro ao exportar jogos do Playnite: $_"
    }
}


