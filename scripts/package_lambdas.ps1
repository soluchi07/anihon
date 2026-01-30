$ErrorActionPreference = "Stop"

# Packages Lambda handlers into zip files for deployment
$root = Resolve-Path "$PSScriptRoot\.."
$lambdaRoot = Join-Path $root "backend\lambdas"
$outDir = Join-Path $root "build\lambdas"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Get-ChildItem -Path $lambdaRoot -Directory | ForEach-Object {
    $name = $_.Name
    $src = $_.FullName
    $zip = Join-Path $outDir ("$name.zip")

    if (Test-Path $zip) { Remove-Item $zip -Force }

    Write-Host "Packaging $name -> $zip"
    Compress-Archive -Path (Join-Path $src "*") -DestinationPath $zip
}

Write-Host "Done. Zips are in $outDir"