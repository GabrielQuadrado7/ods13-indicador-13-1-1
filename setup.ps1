<#
.SYNOPSIS
    Prepara o projeto ODS13 numa máquina nova: .venv, dependências, .env e bancos.

.DESCRIPTION
    Pode ser executado várias vezes: pula o que já existe.
      1. Cria o ambiente Python .venv e instala o requirements.txt
      2. Pede a senha do PostgreSQL e cria o .env (se ainda não existir)
      3. Cria os bancos ods13 e ods13_teste (se ainda não existirem)
      4. Com -Carregar, roda também a carga da planilha e a análise

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\setup.ps1
    powershell -ExecutionPolicy Bypass -File .\setup.ps1 -Carregar
#>
param(
    [string]$Senha,              # senha do usuário postgres; se omitida, é perguntada
    [string]$Usuario = "postgres",
    [string]$Servidor = "localhost",
    [int]$Porta = 5432,
    [switch]$Carregar            # roda etl\carregar.py e analise\analisar.py no final
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Passo($texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }
function Ok($texto)    { Write-Host "    $texto" -ForegroundColor Green }
function Falha($texto) { Write-Host "    ERRO: $texto" -ForegroundColor Red; exit 1 }

function Psql {
    # PowerShell 5.1 transforma o stderr de programas externos em exceção; aqui o erro é tratado pelo código de saída
    $anterior = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { & $script:psqlExe -U $Usuario -h $Servidor -p $Porta -d postgres @args 2>$null }
    finally { $ErrorActionPreference = $anterior }
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

# ------------------------------------------------------------------ 1. Python
Passo "Ambiente Python (.venv)"
if (-not (Test-Path $python)) {
    $base = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $base) { Falha "Python não encontrado. Instale o Python 3.13 (marque 'Add to PATH')." }
    & $base.Source -m venv .venv
    if ($LASTEXITCODE -ne 0) { Falha "não foi possível criar o .venv" }
    Ok ".venv criado"
} else {
    Ok ".venv já existe"
}
& $python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { Falha "falha ao instalar as dependências do requirements.txt" }
Ok "dependências instaladas"

# ------------------------------------------------------------------ 2. PostgreSQL
Passo "PostgreSQL"
$psql = Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\psql.exe" -ErrorAction SilentlyContinue |
        Sort-Object { [int]$_.Directory.Parent.Name } -Descending | Select-Object -First 1
if ($null -eq $psql) { Falha "psql.exe não encontrado em C:\Program Files\PostgreSQL. Instale o PostgreSQL 18." }
$script:psqlExe = $psql.FullName
Ok "psql: $($psql.FullName)"

if ([string]::IsNullOrEmpty($Senha)) {
    $seguro = Read-Host "    Senha do usuário '$Usuario' do PostgreSQL" -AsSecureString
    $Senha = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($seguro))
}
$env:PGPASSWORD = $Senha
$env:PGCLIENTENCODING = "UTF8"

Psql -tAc "SELECT 1" | Out-Null
if ($LASTEXITCODE -ne 0) { Falha "não conectou ao PostgreSQL. Confira a senha e se o serviço postgresql-x64-* está rodando." }
Ok "conexão OK"

# ------------------------------------------------------------------ 3. .env
Passo "Arquivo .env"
if (Test-Path ".env") {
    Ok ".env já existe (não foi alterado)"
} else {
    $s = [uri]::EscapeDataString($Senha)
    $base = "postgresql+psycopg://${Usuario}:$s@${Servidor}:$Porta"
    $conteudo = "DATABASE_URL=$base/ods13`nODS13_TEST_DATABASE_URL=$base/ods13_teste`n"
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot ".env"), $conteudo, (New-Object Text.UTF8Encoding $false))
    Ok ".env criado"
}

# ------------------------------------------------------------------ 4. bancos
Passo "Bancos de dados"
foreach ($banco in @("ods13", "ods13_teste")) {
    $existe = Psql -tAc "SELECT 1 FROM pg_database WHERE datname = '$banco'"
    if ("$existe".Trim() -eq "1") {
        Ok "$banco já existe"
    } else {
        Psql -qc "CREATE DATABASE $banco ENCODING 'UTF8' TEMPLATE template0"
        if ($LASTEXITCODE -ne 0) { Falha "não foi possível criar o banco $banco" }
        Ok "$banco criado"
    }
}
Remove-Item Env:PGPASSWORD

# ------------------------------------------------------------------ 5. carga (opcional)
if ($Carregar) {
    $env:PYTHONIOENCODING = "utf-8"
    Passo "Carga da planilha (etl\carregar.py)"
    & $python etl\carregar.py
    if ($LASTEXITCODE -ne 0) { Falha "a carga falhou (veja a mensagem acima)" }
    Passo "Análise (analise\analisar.py)"
    & $python analise\analisar.py
    if ($LASTEXITCODE -ne 0) { Falha "a análise falhou (veja a mensagem acima)" }
}

Write-Host "`nPronto!" -ForegroundColor Green
if (-not $Carregar) {
    Write-Host "Próximos passos:"
    Write-Host "  .venv\Scripts\python etl\carregar.py"
    Write-Host "  .venv\Scripts\python analise\analisar.py"
}
