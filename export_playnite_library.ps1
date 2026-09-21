<#
.SYNOPSIS
    Script auxiliar para exportar jogos da biblioteca do Playnite para playnite_games.json.
.DESCRIPTION
    Lê o banco de dados do Playnite (games.db via LiteDB) e salva em playnite_games.json
    para leitura ultra-rápida pelo choose_random_game.py sem concorrência de processos.
#>

param (
    [string]$PlaynitePath = "E:\Util\Playnite",
    [string]$OutputFile = "$PSScriptRoot\playnite_games.json",
    [switch]$OnlyInstalled = $true
)

$dbPath = Join-Path $PlaynitePath "library\games.db"
$dllPath = Join-Path $PlaynitePath "LiteDB.dll"

if (-not (Test-Path $dbPath)) {
    Write-Warning "Banco de dados do Playnite nao encontrado em: $dbPath"
    exit 1
}

if (-not (Test-Path $dllPath)) {
    Write-Warning "LiteDB.dll nao encontrado em: $dllPath"
    exit 1
}

Write-Host "Carregando biblioteca do Playnite..." -ForegroundColor Cyan

# Copia temporaria para contornar lock se o Playnite estiver em execucao
$tempDb = Join-Path $env:TEMP "playnite_games_export_temp.db"
try {
    # Tenta copiar direto ou com modo compartilhado
    Copy-Item -Path $dbPath -Destination $tempDb -Force -ErrorAction Stop
} catch {
    Write-Warning "O Playnite esta com o banco aberto exclusivamente. Feche o Playnite momentaneamente para sincronizar, ou aguarde o encerramento."
    exit 1
}

try {
    Add-Type -Path $dllPath
    $db = New-Object LiteDB.LiteDatabase($tempDb)
    $col = $db.GetCollection("games")
    $allGames = $col.FindAll()

    $exportList = @()
    foreach ($g in $allGames) {
        $isInstalled = [bool]$g["IsInstalled"].AsBoolean
        if ($OnlyInstalled -and (-not $isInstalled)) {
            continue
        }

        $item = [PSCustomObject]@{
            Id = $g["_id"].AsString
            Name = $g["Name"].AsString
            IsInstalled = $isInstalled
            Playtime = if ($g["Playtime"]) { $g["Playtime"].AsInt64 } else { 0 }
            PlayCount = if ($g["PlayCount"]) { $g["PlayCount"].AsInt32 } else { 0 }
            CoverImage = if ($g["CoverImage"]) { $g["CoverImage"].AsString } else { "" }
            Icon = if ($g["Icon"]) { $g["Icon"].AsString } else { "" }
        }
        $exportList += $item
    }

    $db.Dispose()
    $exportList | ConvertTo-Json -Depth 3 | Set-Content -Path $OutputFile -Encoding UTF8
    Write-Host "Sucesso! Foram exportados $($exportList.Count) jogos para $OutputFile" -ForegroundColor Green
} finally {
    if (Test-Path $tempDb) {
        Remove-Item $tempDb -Force -ErrorAction SilentlyContinue
    }
}
