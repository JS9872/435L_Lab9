param(
    [string]$InputDocument = 'lab9_Joey_Saade.docx',
    [string]$OutputDirectory = 'report_qa'
)
$ErrorActionPreference = 'Stop'
$documentPath = (Resolve-Path -LiteralPath $InputDocument).Path
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$outputPath = (Resolve-Path -LiteralPath $OutputDirectory).Path
$pdfPath = Join-Path $outputPath ([IO.Path]::GetFileNameWithoutExtension($documentPath) + '.pdf')
$helperPath = Join-Path $outputPath 'render.vbs'
# Windows Script Host supplies reliable apartment-threaded Word automation.
@'
Option Explicit
Dim app, doc, args
Set args = WScript.Arguments
Set app = CreateObject("Word.Application")
app.Visible = False
app.DisplayAlerts = 0
Set doc = app.Documents.Open(args(0), False, True)
doc.SaveAs2 args(1), 17
doc.Close False
app.Quit
'@ | Set-Content -LiteralPath $helperPath -Encoding ASCII
& cscript.exe //nologo $helperPath $documentPath $pdfPath
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $pdfPath)) {
    throw 'Microsoft Word PDF export failed.'
}
Write-Output "Rendered PDF: $pdfPath"
