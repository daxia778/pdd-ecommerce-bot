#!/usr/bin/env bash
# ============================================================
#  PDD 电商 AI 客服 — macOS .app 启动器生成脚本
#  执行此脚本后, 桌面会生成 "PDD AI 客服.app"
#  双击即可一键启动 / 停止 / 打开管理后台
# ============================================================

BOT_DIR="/Users/admin/Desktop/pdd-e-commerce-bot"
APP_NAME="PDD AI 客服"
APP_PATH="/Applications/${APP_NAME}.app"
LAUNCH_SH="${BOT_DIR}/launch.sh"

echo "🔨 正在生成 ${APP_NAME}.app ..."

# ── 1. 目录结构 ──────────────────────────────────────────────
mkdir -p "${APP_PATH}/Contents/MacOS"
mkdir -p "${APP_PATH}/Contents/Resources"

# ── 2. Info.plist ────────────────────────────────────────────
cat > "${APP_PATH}/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>             <string>PDD AI 客服</string>
    <key>CFBundleDisplayName</key>      <string>PDD AI 客服</string>
    <key>CFBundleIdentifier</key>       <string>com.pdd.aics.launcher</string>
    <key>CFBundleVersion</key>          <string>2.0</string>
    <key>CFBundleShortVersionString</key><string>2.0</string>
    <key>CFBundleExecutable</key>       <string>launcher</string>
    <key>CFBundleIconFile</key>         <string>AppIcon</string>
    <key>NSHighResolutionCapable</key>  <true/>
    <key>LSUIElement</key>              <false/>
</dict>
</plist>
PLIST

# ── 3. 主执行脚本 (AppleScript → Terminal) ───────────────────
cat > "${APP_PATH}/Contents/MacOS/launcher" << LAUNCHER
#!/bin/bash
# 独立 PDD AI 客服 启动器
BOT_DIR="${BOT_DIR}"
LAUNCH_SH="${LAUNCH_SH}"

osascript << 'EOF'
tell application "Terminal"
    activate
    set newTab to do script ""
    delay 0.3
    do script "clear && echo ''" in newTab
    do script "bash -c 'source ~/.zshrc 2>/dev/null; source ~/.bash_profile 2>/dev/null; true'" in newTab
end tell
EOF

osascript - "${BOT_DIR}" "${LAUNCH_SH}" << 'ASCRIPT'
on run argv
    set botDir to item 1 of argv
    set launchSh to item 2 of argv
    
    set menuChoice to button returned of (display dialog "🛍️  PDD 电商 AI 智能客服启动器 v2

请选择操作：" ¬
        with title "PDD AI 客服" ¬
        buttons {"🔴 停止服务", "📊 打开管理后台", "🟢 启动服务"} ¬
        default button "🟢 启动服务" ¬
        with icon note)
    
    if menuChoice is "🟢 启动服务" then
        tell application "Terminal"
            activate
            set win to do script "cd " & quoted form of botDir & " && bash " & quoted form of launchSh & " start"
            set custom title of win to "PDD AI 客服 — 启动中"
        end tell
        delay 8
        open location "http://localhost:8000/admin"
        
    else if menuChoice is "🔴 停止服务" then
        tell application "Terminal"
            activate
            set win to do script "cd " & quoted form of botDir & " && bash " & quoted form of launchSh & " stop"
            set custom title of win to "PDD AI 客服 — 停止"
        end tell
        
    else if menuChoice is "📊 打开管理后台" then
        open location "http://localhost:8000/admin"
    end if
end run
ASCRIPT
LAUNCHER

chmod +x "${APP_PATH}/Contents/MacOS/launcher"

# ── 4. 生成 PNG 图标 (简单 sips 方案) ────────────────────────
ICON_SCRIPT="${APP_PATH}/Contents/MacOS/mkicon.sh"
ICON_SRC="${BOT_DIR}/scripts/app_icon.png"
ICONSET="${APP_PATH}/Contents/Resources/AppIcon.iconset"

# 先检查是否有 ImageMagick
if command -v convert &>/dev/null && [[ -f "${ICON_SRC}" ]]; then
    mkdir -p "${ICONSET}"
    for SIZE in 16 32 64 128 256 512; do
        convert "${ICON_SRC}" -resize "${SIZE}x${SIZE}" "${ICONSET}/icon_${SIZE}x${SIZE}.png"
        convert "${ICON_SRC}" -resize "$((SIZE*2))x$((SIZE*2))" "${ICONSET}/icon_${SIZE}x${SIZE}@2x.png"
    done
    iconutil -c icns -o "${APP_PATH}/Contents/Resources/AppIcon.icns" "${ICONSET}"
    rm -rf "${ICONSET}"
    echo "  ✅ 图标已生成"
else
    echo "  ℹ️  跳过图标生成（无 ImageMagick 或无源图）"
fi

# ── 5. 完成 ──────────────────────────────────────────────────
echo ""
echo "✅ 启动器已生成: ${APP_PATH}"
echo ""
echo "   双击 App 即可启动 / 停止服务，或直接打开管理后台。"
echo "   App 位置: Applications 文件夹 (已自动放置)"
echo ""
# 刷新 Launchpad
touch "${APP_PATH}"
echo "   (如 Dock 中看不到，请从 Applications 文件夹拖入 Dock)"
echo ""
