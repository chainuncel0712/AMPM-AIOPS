#!/bin/bash
# GitHub Packages 認證設定 — 公倉 chainuncel0712/AMPM-AIOPS
# Usage: source packages/setup_auth.sh
# (source 才能讓 export 生效)

set -euo pipefail

# 從 .env 載入 token
if [ -f .env ]; then
    set -a; source .env; set +a
fi

if [ -z "${GITHUB_API_KEY:-}" ]; then
    echo "❌ 需要設定 GITHUB_API_KEY"
    exit 1
fi

OWNER="chainuncel0712"
REPO="AMPM-AIOPS"
GHCR="${OWNER,,}"  # ghcr.io 只接受小寫

echo "=== GitHub Packages 認證設定 ==="
echo "  帳號: $OWNER"
echo "  倉庫: $REPO"
echo ""

# ── 1. npm ──────────────────────────────────────
cat > .npmrc << EOF
registry=https://npm.pkg.github.com/${OWNER}
//npm.pkg.github.com/:_authToken=\${GITHUB_API_KEY}
always-auth=true
EOF
echo "✅ .npmrc 已建立 （npm publish 用）"

# ── 2. Docker ───────────────────────────────────
echo "$GITHUB_API_KEY" | docker login ghcr.io -u "$OWNER" --password-stdin 2>/dev/null && \
    echo "✅ Docker 已登入 ghcr.io (docker push ghcr.io/${GHCR}/... 用)" || \
    echo "⚠️  docker login 失敗（可能沒裝 docker）"

# ── 3. NuGet ────────────────────────────────────
cat > nuget.config << EOF
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <clear />
    <add key="github" value="https://nuget.pkg.github.com/${OWNER}/index.json" />
  </packageSources>
</configuration>
EOF
echo "✅ nuget.config 已建立 (dotnet nuget push 用，token 用 --api-key 傳)"

# ── 4. RubyGems ─────────────────────────────────
mkdir -p ~/.gem
cat > ~/.gem/credentials << EOF
---
:github: Bearer ${GITHUB_API_KEY}
EOF
chmod 600 ~/.gem/credentials
echo "✅ ~/.gem/credentials 已建立 (gem push 用)"

# ── 5. Maven ────────────────────────────────────
mkdir -p ~/.m2
cat > ~/.m2/settings.xml << EOF
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0
                              http://maven.apache.org/xsd/settings-1.0.0.xsd">
  <servers>
    <server>
      <id>github</id>
      <username>${OWNER}</username>
      <password>${GITHUB_API_KEY}</password>
    </server>
  </servers>
</settings>
EOF
echo "✅ ~/.m2/settings.xml 已建立 (mvn deploy 用)"

echo ""
echo "=== 全部完成 ==="
echo "可用的推送指令："
echo ""
echo "  npm:     npm publish"
echo "  Docker:  docker push ghcr.io/${GHCR}/<image>:<tag>"
echo "  NuGet:   dotnet nuget push <nupkg> --source github --api-key \$GITHUB_API_KEY"
echo "  Gem:     gem push --key github --host https://rubygems.pkg.github.com/${OWNER} <gem>"
echo "  Maven:   mvn deploy"
