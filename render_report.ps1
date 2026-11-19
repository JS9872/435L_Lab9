param(
    [string]$InputDocument = 'lab9_Joey_Saade.docx',
    [string]$OutputDirectory = 'report_qa'
)
$ErrorActionPreference = 'Stop'
$documentPath = (Resolve-Path -LiteralPath $InputDocument).Path
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$outputPath = (Resolve-Path -LiteralPath $OutputDirectory).Path
$pdfPath = Join-Path $outputPath ([IO.Path]::GetFileNameWithoutExtension($documentPath) + '.pdf')
$wordApp = New-Object -ComObject Word.Application
$wordApp.Visible = $false
$wordApp.DisplayAlerts = 0
try {
    $document = $wordApp.Documents.Open($documentPath, $false, $true)
    $document.Repaginate()
    $document.ExportAsFixedFormat($pdfPath, 17)
    Write-Output "Rendered pages: $($document.ComputeStatistics(2))"
    $document.Close(0)
} finally {
    $wordApp.Quit()
}
Write-Output "Rendered PDF: $pdfPath"
