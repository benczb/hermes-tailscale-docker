# Validate real profile-name selection, saved defaults and explicit overrides without installing apps.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'setup-windows.ps1'),[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw 'Installer parse failure' }
foreach ($node in $ast.FindAll({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst]},$true)) { . ([scriptblock]::Create($node.Extent.Text)) }
foreach ($valid in @('Hamburger','ben-personal','Ben_01','a',('a'*64))) { if (-not (Test-WorkshopProfileName $valid)) { throw 'Valid profile rejected' } }
foreach ($invalid in @('','hermes','Hermes','default','Default','test','Test','tmp','root','sudo','CON','nul','COM1','Lpt9','../x','a/b','a\b','a b','-option',('a'*65))) { if (Test-WorkshopProfileName $invalid) { throw 'Unsafe or reserved profile accepted' } }
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('hermes profile names ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixture | Out-Null
$file=Join-Path $fixture 'last-profile'
$answers=New-Object 'System.Collections.Generic.Queue[string]'
$prompts=New-Object 'System.Collections.Generic.List[string]'
function Read-Host { param($Prompt) $prompts.Add($Prompt); if (-not $answers.Count) { throw 'Unexpected name prompt' }; return $answers.Dequeue() }
try {
    foreach ($answer in @('bad/name','CON','Default','test','  Hamburger_01  ')) { $answers.Enqueue($answer) }
    $selected=Select-WorkshopProfileName '' $file
    if ($selected -ne 'Hamburger_01' -or $prompts.Count -ne 5) { throw 'Prompt validation/custom selection failed' }
    if ((Get-Content $file -Raw) -ne $selected) { throw 'Custom name was not saved' }
    $answers.Enqueue('')
    if ((Select-WorkshopProfileName '' $file) -ne $selected -or $prompts[-1] -notlike '*Hamburger_01*') { throw 'Rerun did not reuse the saved default' }
    $before=$prompts.Count
    if ((Select-WorkshopProfileName 'personal' $file) -ne 'personal' -or $prompts.Count -ne $before) { throw 'Explicit name did not bypass the prompt' }
    $failed=$false; try { Select-WorkshopProfileName '../bad' $file } catch { $failed=$true }
    if (-not $failed -or (Get-Content $file -Raw) -ne 'personal') { throw 'Invalid explicit input changed the saved selection' }
    Save-Utf8 $file '../bad'
    $answers.Enqueue('')
    if ((Select-WorkshopProfileName '' $file) -ne 'starter-agent') { throw 'Invalid saved default was trusted' }
    Save-Utf8 $file 'test'
    $answers.Enqueue('')
    if ((Select-WorkshopProfileName '' $file) -ne 'starter-agent') { throw 'A saved upstream-reserved name was reused' }
    Save-Utf8 $file 'workshop'
    $answers.Enqueue('')
    if ((Select-WorkshopProfileName '' $file) -ne 'workshop') { throw 'Existing workshop selection was not preserved' }
    Write-Host 'Profile name tests passed: safe names, retries, saved defaults and explicit overrides.'
} finally { Remove-Item -LiteralPath $fixture -Recurse -Force }
