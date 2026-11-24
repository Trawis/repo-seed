# PowerShell Conventions

**Document role**: Managed coding-agent reference
**Sync destination**: `.agents/conventions/powershell.md`
**Local editing**: Do not customize this synced copy

Apply repository rules first. Use this with `.agents/conventions/scripts.md`.
Configured PSScriptAnalyzer settings, formatter settings, and nearby scripts
take precedence. POSIX shell and Bash belong to `.agents/conventions/shell.md`.

## Compatibility

- Target the editions and versions the project supports: Windows PowerShell
  5.1 (`Desktop`), PowerShell 7+ (`Core`), or both. Declare requirements with
  `#Requires -Version` or the module manifest's `CompatiblePSEditions`.
- Do not use 7+ syntax, such as `??`, `?.`, ternaries, or `ForEach-Object
  -Parallel`, in scripts that must run on 5.1.
- For cross-platform scripts, avoid Windows-only cmdlets and paths, and do not
  assume case-insensitive file systems.
- Set file encodings explicitly with `-Encoding`; 5.1 and 7+ use different
  defaults.

## Naming and Structure

- Name functions `Verb-Noun` with an approved verb (`Get-Verb`) and a singular
  noun. Use `PascalCase` for functions and parameters.
- Use full cmdlet and parameter names in scripts, not aliases or positional
  shortcuts.
- Make reusable functions advanced functions with `[CmdletBinding()]` and a
  `param()` block. Validate parameters with `[Parameter(Mandatory)]`,
  `[ValidateSet()]`, `[ValidateNotNullOrEmpty()]`, and typed parameters.

## Pipeline and Output

- Emit objects, not formatted text. Do not call `Format-*` in functions whose
  output other code consumes.
- Use `Write-Output` or implicit output for data, and `Write-Verbose`,
  `Write-Warning`, `Write-Error`, or `Write-Information` for messages. Do not
  use `Write-Host` for data.
- Suppress unwanted output with `$null =` or `[void]` so that it does not leak
  into the function's return value.

## Errors and Exit Codes

- Set `$ErrorActionPreference = 'Stop'` in scripts, or pass `-ErrorAction Stop`,
  so that non-terminating errors do not pass silently. Handle expected
  failures with `try`/`catch`.
- Check `$LASTEXITCODE` after native commands; they do not raise PowerShell
  errors by default.
- End scripts with explicit `exit` codes when callers depend on them.

## Paths, Quoting, and Safety

- Build paths with `Join-Path`, and use `-LiteralPath` for paths that may
  contain wildcard characters such as `[` and `]`.
- Use single quotes for literal strings and double quotes only for
  interpolation.
- Do not use `Invoke-Expression` with constructed strings. Call commands with
  argument arrays or splatting.
- Support `-WhatIf` and `-Confirm` with `SupportsShouldProcess` and
  `$PSCmdlet.ShouldProcess` for functions that change state, and set
  `ConfirmImpact` for destructive operations.
- Accept credentials as `[PSCredential]`. Do not take plain-text password
  parameters, convert plain text to `SecureString`, or write secrets to logs.

## Documentation and Validation

- Give reusable functions and scripts comment-based help with `.SYNOPSIS`,
  `.DESCRIPTION`, `.PARAMETER`, and `.EXAMPLE`.
- Run `Invoke-ScriptAnalyzer` with the project's settings and the configured
  Pester tests. Test with each supported edition when practical.

## References

- [PSScriptAnalyzer rules and recommendations](https://learn.microsoft.com/en-us/powershell/utility-modules/psscriptanalyzer/rules-recommendations)
- [Approved verbs](https://learn.microsoft.com/en-us/powershell/scripting/developer/cmdlet/approved-verbs-for-windows-powershell-commands)
- [Everything about ShouldProcess](https://learn.microsoft.com/en-us/powershell/scripting/learn/deep-dives/everything-about-shouldprocess)
- [Differences from Windows PowerShell](https://learn.microsoft.com/en-us/powershell/scripting/whats-new/differences-from-windows-powershell)
- [Pester](https://pester.dev/docs/quick-start)
