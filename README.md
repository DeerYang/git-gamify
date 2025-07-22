
<div align="right">
  <b><a href="README.md">English</a></b> | <a href="README_zh.md">中文</a>
</div>

<br>

<div align="center">
  <h1 align="center">🎮 Git-Gamify</h1>
  <p align="center">
    Turn your command-line Git workflow into a fun RPG!
    <br />
    Level up, unlock achievements, and make every commit rewarding.
  </p>
</div>

<p align="center">
  <img src="https://img.shields.io/pypi/v/git-gamify.svg?color=blue" alt="PyPI Version">
  <img src="https://img.shields.io/pypi/pyversions/git-gamify.svg" alt="Python Versions">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

---

<img width="1110" height="622" alt="Image" src="https://github.com/user-attachments/assets/00cd62d4-2984-43ca-87c1-e8683c419b5c" />

## ✨ What is Git-Gamify?

Git-Gamify is a command-line tool that adds a fun gamification layer to your daily Git usage. It silently wraps your `git` commands (`commit`, `push`, etc.) and rewards you with Experience Points (XP), levels, and achievements, turning tedious tasks into an engaging game.

## 🚀 Key Features

- **Leveling System**: Gain XP for `commit` and `push` actions and watch your level grow.
- **Dynamic XP**: Earn bonus XP for commit streaks and the volume of your code changes.
- **Achievement Engine**: Unlock over a dozen achievements for milestones, consistency, and special actions.
- **Rich Profile**: View your progress, stats, and unlocked achievements with a beautifully formatted profile.
- **Multi-language**: Supports both English and Chinese.
- **Lightweight & Fast**: Runs silently in the background without slowing you down.

## 📦 Installation

Git-Gamify requires Python 3.8+ and Git to be installed on your system.

You can install it directly from PyPI using `pip`:

```bash
pip install git-gamify 
```

## ⚙️ Configuration

To let Git-Gamify track your commands, you need to set up a function in your shell's configuration file.

### Step 1: Required Alias Setup (Crucial!)

This is the only required setup step. Choose the one for your shell.

**For PowerShell:**
Open your profile with `notepad $PROFILE` and add the following line:

```powershell
function git {
    gg git @args
}
```

**For Bash / Zsh:**
Open your `~/.bashrc` or `~/.zshrc` file and add the following function:

```bash
function git() {
    gg git "$@"
}
```

> **⚠️ Important:** After pasting the function, please ensure you press **Enter** to add a new line at the end of the file. This prevents issues if other scripts are added later.

After saving the file, **restart your terminal** for the changes to take effect.

### Step 2: Optional - Enable Autocompletion

For a much smoother experience, we highly recommend installing the autocompletion script. After completing Step 1 and restarting your terminal, run the appropriate command:

**For PowerShell:** `gg --install-completion powershell`
**For Bash:** `gg --install-completion bash`
**For Zsh:** `gg --install-completion zsh`

Follow any on-screen instructions, then **restart your terminal one last time**.

## 🎮 Commands Guide

Once configured, your `git` commands will automatically grant XP! You can also use Git-Gamify's internal commands:

### `gg profile`
Displays your complete user profile, including level, XP progress, and unlocked achievements.

```bash
gg profile
```
**Options:**
- `--stats` or `-s`: Display detailed statistics only (total commits, pushes, etc.).
  ```bash
  gg profile --stats
  ```
- `--reset`: Resets all progress for the current user (requires confirmation).
  ```bash
  gg profile --reset
  ```

### `gg config`
Gets or sets configuration values.

**Usage:**
- **Set a value:**
  ```bash
  # Set language to Chinese
  gg config --set language=zh
  
  # Set language back to English
  gg config --set language=en
  ```
- **Get a value:**
  ```bash
  gg config --get language
  ```

### `gg help`
Displays the help message with a list of internal commands.

```bash
gg help
```

## 📄 License

This project is licensed under the MIT License.
