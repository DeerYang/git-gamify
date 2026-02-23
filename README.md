<div align="right">
  <b><a href="README.md">English</a></b> | <a href="README_zh.md">中文</a>
</div>

<br>

<div align="center">
  <h1 align="center">Git-Gamify</h1>
  <p align="center">
    Turn your daily Git workflow into a lightweight RPG loop.
    <br />
    Earn XP, level up, and unlock achievements from real Git usage.
  </p>
</div>

<p align="center">
  <img src="https://img.shields.io/pypi/v/git-gamify.svg?color=blue" alt="PyPI Version">
  <img src="https://img.shields.io/pypi/pyversions/git-gamify.svg" alt="Python Versions">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

---

<img width="1110" height="622" alt="Git-Gamify demo" src="https://github.com/user-attachments/assets/00cd62d4-2984-43ca-87c1-e8683c419b5c" />

## What Is Git-Gamify

Git-Gamify wraps your normal `git` usage (`commit`, `push`) and adds a game layer:

- XP and level progression
- achievement unlocks
- reward messages on level up
- profile/stat display commands

The core goal is to keep your existing Git habits intact while adding immediate feedback and motivation.

## Features

- Progressive XP system for commits and pushes
- Daily decay/cap mechanics to avoid farming
- Streak and behavior-based achievements
- Local profile persistence per Git identity (`user.email`)
- Multi-language support (`en`, `zh`)
- Rich terminal UI output

## Installation

Requirements:

- Python 3.8+
- Git

Install from PyPI:

```bash
pip install git-gamify
```

Or install this repo in editable mode:

```bash
pip install -e .
```

## Quick Start

1. Add shell wrapper so your normal `git` command is routed through Git-Gamify.
2. Restart terminal.
3. Use Git as usual (`git commit`, `git push`).
4. Check progress with `gg profile`.

## Shell Setup

### PowerShell (Required)

Edit your profile:

```powershell
notepad $PROFILE
```

Add:

```powershell
function git {
    gg git @args
}
```

Restart PowerShell.

### Bash / Zsh (Required)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
function git() {
    gg git "$@"
}
```

Reload shell (`source ~/.bashrc` / `source ~/.zshrc`) or restart terminal.

## Autocompletion

### CLI Completion for `gg`

Run once:

```powershell
gg --install-completion powershell
```

(`bash` and `zsh` are also supported via Typer installer.)

### PowerShell: Keep Both `gg` and Wrapped `git` Completion

When `git` is wrapped as a PowerShell function, default `git` completion can disappear because completion was attached to native `git.exe`, not your function.

Use this profile setup:

```powershell
Import-Module PSReadLine
Import-Module posh-git
$GitPromptSettings.EnablePromptStatus = $false

function git {
    gg git @args
}

Set-PSReadLineKeyHandler -Chord Tab -Function MenuComplete

# gg completion
$scriptblock = {
    param($wordToComplete, $commandAst, $cursorPosition)
    $Env:_GG_COMPLETE = "complete_powershell"
    $Env:_TYPER_COMPLETE_ARGS = $commandAst.ToString()
    $Env:_TYPER_COMPLETE_WORD_TO_COMPLETE = $wordToComplete
    gg | ForEach-Object {
        $commandArray = $_ -Split ":::"
        $command = $commandArray[0]
        $helpString = $commandArray[1]
        [System.Management.Automation.CompletionResult]::new(
            $command, $command, "ParameterValue", $helpString
        )
    }
    $Env:_GG_COMPLETE = ""
    $Env:_TYPER_COMPLETE_ARGS = ""
    $Env:_TYPER_COMPLETE_WORD_TO_COMPLETE = ""
}
Register-ArgumentCompleter -Native -CommandName gg -ScriptBlock $scriptblock

# bridge completion for wrapped git function
Register-ArgumentCompleter -CommandName git -ScriptBlock {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
    $line = $commandAst.ToString()
    $lastWord = $wordToComplete
    GitTabExpansion $line $lastWord | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, "ParameterValue", $_)
    }
}
```

Notes:

- `Import-Module posh-git` is required for `GitTabExpansion`.
- If startup throws `cannot find 'gg'`, ensure `gg` is installed in the active Python environment and available in `PATH`.
- `main`/branch text in prompt is from `posh-git` prompt feature, not Git-Gamify runtime.

## Commands

### `gg profile`

Show user profile, level progress, and unlocked achievements.

```bash
gg profile
```

Options:

- `gg profile --stats` or `gg profile -s`
- `gg profile --reset`

### `gg config`

Read or update config values.

```bash
gg config --get language
gg config --set language=zh
gg config --set language=en
```

### `gg help`

Show internal command help.

```bash
gg help
```

## Data Storage

User data is stored locally under:

- Windows: `%USERPROFILE%\.git-gamify`
- Unix-like: `~/.git-gamify`

Profiles are keyed by a hash of your Git `user.email`.

## Development

Create and use a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pip install pytest
pytest -q -p no:cacheprovider
```

## License

MIT License.
