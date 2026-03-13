<div align="right">
  <a href="README.md">English</a> | <b><a href="README_zh.md">中文</a></b>
</div>

<br>

<div align="center">
  <h1 align="center">Git-Gamify</h1>
  <p align="center">
    把你每天的 Git 工作流变成一个轻量 RPG 循环。
    <br />
    通过真实 Git 操作获得经验值、升级并解锁成就。
  </p>
</div>

<p align="center">
  <img src="https://img.shields.io/pypi/v/git-gamify.svg?color=blue" alt="PyPI 版本">
  <img src="https://img.shields.io/pypi/pyversions/git-gamify.svg" alt="Python 版本">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="许可证">
</p>

---

<img width="834" height="364" alt="Image" src="https://github.com/user-attachments/assets/871085f4-4abc-4551-911c-a836e640ce09" />

## Git-Gamify 是什么

Git-Gamify 会包装你平时的 `git` 使用（如 `commit`、`push`），并叠加一层游戏化反馈：

- 经验值与等级成长
- 成就解锁
- 升级时随机奖励提示
- 个人资料与统计展示

核心目标是保留你原有 Git 习惯，不改操作心智，同时提供即时反馈和长期动力。

## 功能特性

- 面向 `commit` 和 `push` 的 XP 成长体系
- 每日衰减/上限机制，避免刷分
- 连击与行为驱动成就系统
- 基于 Git 身份（`user.email`）的本地独立档案
- 多语言支持（`en`、`zh`）
- Rich 终端 UI 展示

## 安装

环境要求：

- Python 3.8+
- Git

通过 PyPI 安装：

```bash
pip install git-gamify
```

或在本仓库可编辑安装：

```bash
pip install -e .
```

## 快速开始

1. 在 Shell 中配置 `git` 包装函数，让命令经过 Git-Gamify。
2. 重启终端。
3. 像平时一样使用 Git（`git commit`、`git push`）。
4. 用 `gg profile` 查看成长进度。

## Shell 配置

### PowerShell（必需）

编辑 PowerShell 配置：

```powershell
notepad $PROFILE
```

添加：

```powershell
function git {
    gg git @args
}
```

保存后重启 PowerShell。

### Bash / Zsh（必需）

在 `~/.bashrc` 或 `~/.zshrc` 添加：

```bash
function git() {
    gg git "$@"
}
```

然后执行 `source ~/.bashrc` / `source ~/.zshrc` 或重启终端。

## 命令补全

### `gg` 命令补全

首次执行：

```powershell
gg --install-completion powershell
```

（`bash` 和 `zsh` 也支持 Typer 的补全安装。）

### PowerShell 下同时保留 `gg` 与包装后 `git` 的补全

当你把 `git` 包装成 PowerShell 函数后，原生 `git` 补全可能失效。原因是补全原本绑定在 `git.exe`，而不是你的函数。

可使用下面的 `Microsoft.PowerShell_profile.ps1` 配置：

```powershell
Import-Module PSReadLine
Import-Module posh-git
$GitPromptSettings.EnablePromptStatus = $false

function git {
    gg git @args
}

Set-PSReadLineKeyHandler -Chord Tab -Function MenuComplete

# gg 补全
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

# 给包装后的 git 函数桥接 posh-git 补全
Register-ArgumentCompleter -CommandName git -ScriptBlock {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
    $line = $commandAst.ToString()
    $lastWord = $wordToComplete
    GitTabExpansion $line $lastWord | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, "ParameterValue", $_)
    }
}
```

说明：

- `GitTabExpansion` 由 `posh-git` 提供，所以必须 `Import-Module posh-git`。
- 如果启动时提示找不到 `gg`，说明当前 Python 环境里没有安装或 `PATH` 未包含可执行路径。
- 提示符中的 `main`/分支信息来自 `posh-git`，不是 Git-Gamify 自身逻辑。

## 命令说明

### `gg profile`

查看用户档案、等级进度和已解锁成就：

```bash
gg profile
```

可选项：

- `gg profile --stats` 或 `gg profile -s`
- `gg profile --reset`

### `gg config`

读取或更新配置：

```bash
gg config --get language
gg config --set language=zh
gg config --set language=en
```

### `gg doctor`

输出本机诊断信息（环境、Git、项目状态），用于排错和 issue 反馈。

```bash
gg doctor
```

### `gg help`

查看内置命令帮助：

```bash
gg help
```

## 数据存储

用户数据默认保存在本地：

- Windows：`%USERPROFILE%\.git-gamify`
- Unix-like：`~/.git-gamify`

每个档案以 Git `user.email` 的哈希值区分。

## 开发与测试

推荐使用虚拟环境：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pip install pytest
pytest -q -p no:cacheprovider
```

## 许可证

MIT License。
