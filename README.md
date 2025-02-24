# HeavyMetal: Homebrew Music streaming server
HeavyMetal is a Homebrew Music streaming Backend server, designed to be simple and run in any (almost) platform.

**Note that you will need a Frontend too that can ask for Content from this Backend.**

## Installation and Usage
1. Install `uv` Package manager first
MacOS, Linux, BSD:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Windows:
```pwsh
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Alternatively you can use `pip` or `pipx`:
```bash
pip install uv
```

```bash
pipx install uv
```
2. Set Environment variables:
`$EDITOR` is the editor of your choice
```bash
cp env.example .env
$EDITOR .env
```
3. Resolve the Dependencies:
```bash
uv sync
uv run python3 .
```
