<div align="right">
  <a href="README.md">English</a> | <b><a href="README_zh.md">中文</a></b>
</div>

<br>

<div align="center">
  <h1 align="center">🎮 Git-Gamify</h1>
  <p align="center">
    将你的命令行 Git 工作流变成一个有趣的 RPG 游戏！
    <br />
    升级、解锁成就，让每一次提交都充满回报。
  </p>
</div>

<p align="center">
  <img src="https://img.shields.io/pypi/v/git-gamify.svg?color=blue" alt="PyPI 版本">
  <img src="https://img.shields.io/pypi/pyversions/git-gamify.svg" alt="Python 版本">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="许可协议">
</p>

---

<img width="1110" height="622" alt="Image" src="https://github.com/user-attachments/assets/00cd62d4-2984-43ca-87c1-e8683c419b5c" />

## ✨ Git-Gamify 是什么？

Git-Gamify 是一个命令行工具，它为你日常的 Git 操作添加了一个有趣的“游戏化”层。它会静默地包装你的 `git` 命令（如 `commit`, `push`），并用经验值（XP）、等级和成就来奖励你，将单调的任务变成一个引人入胜的游戏。

## 🚀 主要特性

- **等级系统**: 通过 `commit` 和 `push` 操作获得经验值，见证你的等级成长。
- **动态经验**: 根据你的连续提交天数和代码改动量获得额外奖励经验。
- **成就引擎**: 解锁超过12个成就，涵盖里程碑、连续性和特殊操作等。
- **内容丰富的个人档案**: 使用精美格式化的个人档案，查看你的进度、统计和已解锁的成就。
- **多语言**: 支持中文和英文。
- **轻量且快速**: 在后台静默运行，不会拖慢你的工作流。

## 📦 安装

Git-Gamify 需要你的系统已安装 Python 3.8+ 和 Git。

你可以直接通过 PyPI 使用 `pip` 来安装：

```bash
pip install git-gamify
```

## ⚙️ 配置

为了让 Git-Gamify 能够追踪你的命令，你需要在你的 Shell 配置文件中设置一个函数。

### 步骤一：必需的别名设置 (关键步骤!)

这是唯一必需的配置步骤。请为你的 Shell 选择对应的配置。

**对于 PowerShell:**
使用 `notepad $PROFILE` 命令打开你的配置文件，并添加以下这行：

```powershell
function git {
    gg git @args
}
```

**对于 Bash / Zsh:**
打开你的 `~/.bashrc` 或 `~/.zshrc` 文件，并添加以下函数：

```bash
function git() {
    gg git "$@"
}
```

> **⚠️ 重要提示:** 粘贴完函数后，请务必按下 **回车键** 以确保在文件末尾添加一个新行。这可以防止以后添加其他脚本时可能出现的问题。

保存文件后，请 **重启你的终端** 以使改动生效。

### 步骤二：可选 - 开启自动补全

为了获得更流畅的命令行体验，我们强烈推荐你安装自动补全脚本。在完成步骤一并重启终端后，运行适合你的命令：

**对于 PowerShell:** `gg --install-completion powershell`
**对于 Bash:** `gg --install-completion bash`
**对于 Zsh:** `gg --install-completion zsh`

请遵循屏幕上的指示完成安装，然后 **最后再重启一次你的终端**。

## 🎮 命令指南

一旦配置完成，你的 `git` 命令就会自动为你增加经验值了！你也可以使用 Git-Gamify 的内部命令：

### `gg profile`
显示你完整的用户档案，包括等级、经验值进度和已解锁的成就。

```bash
gg profile
```
**选项:**
- `--stats` 或 `-s`: 仅显示详细的统计数据（总提交数、推送数等）。
  ```bash
  gg profile --stats
  ```
- `--reset`: 重置当前用户的所有进度（需要确认）。
  ```bash
  gg profile --reset
  ```

### `gg config`
获取或设置配置值。

**用法:**
- **设置一个值:**
  ```bash
  # 设置语言为中文
  gg config --set language=zh
  
  # 设置语言回英文
  gg config --set language=en
  ```
- **获取一个值:**
  ```bash
  gg config --get language
  ```

### `gg help`
显示包含内部命令列表的帮助信息。

```bash
gg help
```

## 📄 许可协议

本项目基于 MIT 许可协议。
