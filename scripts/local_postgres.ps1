param([ValidateSet('start','stop')][string]$Action='start')
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtimeRoot = Join-Path $projectRoot '.runtime'
$clusterPath = Join-Path $runtimeRoot 'pgdata'
$pgBin = if ($env:PG_BIN) { $env:PG_BIN } else { 'C:\Program Files\PostgreSQL\18\bin' }
if (!(Test-Path (Join-Path $pgBin 'pg_ctl.exe'))) { throw 'Set PG_BIN to the PostgreSQL 16+ bin directory' }
if ($Action -eq 'stop') {
    & (Join-Path $pgBin 'pg_ctl.exe') -D $clusterPath stop -m fast
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL stop failed' }
    exit
}
New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null
$envPath = Join-Path $projectRoot '.env'
if (!(Test-Path $envPath)) {
    $randomPassword = [Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(24))
    $exampleText = Get-Content -Raw -LiteralPath (Join-Path $projectRoot '.env.example')
    $exampleText.Replace('PG_PASSWORD=', "PG_PASSWORD=$randomPassword").Replace('AIRFLOW_DB_PASSWORD=', "AIRFLOW_DB_PASSWORD=$randomPassword").Replace('AIRFLOW_ADMIN_PASSWORD=', "AIRFLOW_ADMIN_PASSWORD=$randomPassword") | Set-Content -LiteralPath $envPath -Encoding utf8
}
$configValues = @{}
Get-Content -LiteralPath $envPath | ForEach-Object { if ($_ -match '^([A-Z_]+)=(.*)$') { $configValues[$matches[1]]=$matches[2] } }
if (!$configValues['PG_PASSWORD']) { throw 'Choose PG_PASSWORD in .env before initializing PostgreSQL' }
if (!(Test-Path (Join-Path $clusterPath 'PG_VERSION'))) {
    $passwordFile = Join-Path $runtimeRoot 'init-password'
    [System.IO.File]::WriteAllText($passwordFile,$configValues['PG_PASSWORD'])
    try {
        & (Join-Path $pgBin 'initdb.exe') -D $clusterPath -U $configValues['PG_USER'] --encoding=UTF8 --locale=C --auth=scram-sha-256 --pwfile=$passwordFile
        if ($LASTEXITCODE -ne 0) { throw 'initdb failed' }
    } finally { Remove-Item -LiteralPath $passwordFile -ErrorAction SilentlyContinue }
}
& (Join-Path $pgBin 'pg_ctl.exe') -D $clusterPath status | Out-Null
if ($LASTEXITCODE -ne 0) {
    # pg_ctl launches the server in the background without a visible window.
    & (Join-Path $pgBin 'pg_ctl.exe') -D $clusterPath -l (Join-Path $runtimeRoot 'postgres.log') -o "-p $($configValues['PG_PORT']) -h 127.0.0.1" -w start
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL start failed' }
}
$env:PGPASSWORD = $configValues['PG_PASSWORD']
try {
    $exists = & (Join-Path $pgBin 'psql.exe') -h 127.0.0.1 -p $configValues['PG_PORT'] -U $configValues['PG_USER'] -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='analytics'"
    if ($LASTEXITCODE -ne 0) { throw 'Database connection failed' }
    if (!$exists) {
        & (Join-Path $pgBin 'createdb.exe') -h 127.0.0.1 -p $configValues['PG_PORT'] -U $configValues['PG_USER'] analytics
        if ($LASTEXITCODE -ne 0) { throw 'Database creation failed' }
    }
} finally { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
