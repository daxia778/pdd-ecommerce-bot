#!/usr/bin/env bash
# ============================================================
#   PDD 电商 AI 智能客服  —  专属启动器 v1
#   项目：pdd-e-commerce-bot（/Users/admin/Desktop/pdd-e-commerce-bot）
#   服务：FastAPI + Uvicorn  (port 8000)
#   用法：./launch.sh {start|stop|restart|status|log}
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGDIR"

# PID 文件 —— 独立命名，不与桌面其他启动器冲突
PID_FILE="$SCRIPT_DIR/.pdd_bot.pid"
LOG_FILE="$LOGDIR/pdd_bot.log"

if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
elif [ -f "$SCRIPT_DIR/venv/bin/python3" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python3"
else
    PYTHON_BIN="$(which python3 2>/dev/null || which python)"
fi
MAIN_SCRIPT="$SCRIPT_DIR/main.py"
PORT=8100

# ── 颜色 ────────────────────────────────────────────────────
R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'
B='\033[0;34m'; C='\033[0;36m'; W='\033[1;37m'; N='\033[0m'

# ── 工具 ─────────────────────────────────────────────────────
log()  { echo -e "${W}[$(date '+%H:%M:%S')]${N} $*"; }
ok()   { echo -e "${G}  ✅ $*${N}"; }
warn() { echo -e "${Y}  ⚠️  $*${N}"; }
err()  { echo -e "${R}  ❌ $*${N}"; }
info() { echo -e "${C}  ℹ️  $*${N}"; }

banner() {
  echo -e "${C}"
  echo "  ╔══════════════════════════════════════════════════╗"
  echo "  ║  🛍️  PDD 电商 AI 智能客服  — 专属启动器 v1       ║"
  echo "  ║  FastAPI + SQLite + RAG       port: ${PORT}        ║"
  echo "  ╚══════════════════════════════════════════════════╝${N}"
  echo ""
}

# ── 状态检测 ─────────────────────────────────────────────────
port_listening() { lsof -i ":$1" -sTCP:LISTEN -t &>/dev/null; }

api_healthy() {
  local resp
  resp=$(curl -s --max-time 4 "http://localhost:${PORT}/api/v1/health" 2>/dev/null)
  echo "$resp" | grep -q '"status"'
}

bot_alive() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" &>/dev/null
}

# ── 清理 ─────────────────────────────────────────────────────
kill_pid_file() {
  if [[ -f "$PID_FILE" ]]; then
    local pid; pid=$(<"$PID_FILE")
    kill "$pid" &>/dev/null; sleep 0.5
    kill -9 "$pid" &>/dev/null
    rm -f "$PID_FILE"
  fi
}

# ────────────────────────────────────────────────────────────
# 启动服务
# ────────────────────────────────────────────────────────────
start_bot() {
  log "启动 ${C}PDD AI 客服 (FastAPI)${N} @ 端口 :${PORT}"

  # 若进程健康 → 保留
  if bot_alive && port_listening "$PORT"; then
    ok "服务已在运行 (PID: $(cat "$PID_FILE"))，无需重启。"
    info "管理后台 → http://localhost:${PORT}/admin"
    return 0
  fi

  # 清理残余
  if pgrep -f "main.py" &>/dev/null; then
    warn "检测到残余进程，正在清理..."
    pkill -9 -f "main.py" &>/dev/null; sleep 1
  fi
  if port_listening "$PORT"; then
    warn "端口 ${PORT} 被占用，尝试清理..."
    lsof -ti ":${PORT}" | xargs kill -9 &>/dev/null; sleep 1
  fi
  kill_pid_file

  # 检查入口脚本
  if [[ ! -f "$MAIN_SCRIPT" ]]; then
    err "找不到 main.py: $MAIN_SCRIPT"
    return 1
  fi

  # 启动
  cd "$SCRIPT_DIR"
  nohup "$PYTHON_BIN" "$MAIN_SCRIPT" > "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  log "进程已启动 (PID: $(cat "$PID_FILE"))，等待就绪..."

  # 等待 API 就绪（最多 20 秒）
  echo -n "   健康检查"
  for i in {1..20}; do
    sleep 1; echo -n "."
    if api_healthy; then
      echo ""
      ok "FastAPI 服务就绪 ✓  (${i}s)"
      echo ""
      echo -e "  ${W}▶  访问地址${N}"
      echo -e "    Swagger 文档  →  ${G}http://localhost:${PORT}/docs${N}"
      echo -e "    管理后台      →  ${G}http://localhost:${PORT}/admin${N}"
      echo -e "    健康检查      →  ${G}http://localhost:${PORT}/api/v1/health${N}"
      echo -e "    实时日志      →  ${C}tail -f $LOG_FILE${N}"
      echo ""
      return 0
    fi
  done

  echo ""
  err "服务启动超时！请检查日志："
  tail -20 "$LOG_FILE"
  return 1
}

# ────────────────────────────────────────────────────────────
# 停止服务
# ────────────────────────────────────────────────────────────
stop_bot() {
  log "停止 PDD AI 客服服务..."

  if bot_alive; then
    local pid; pid=$(cat "$PID_FILE")
    kill "$pid" &>/dev/null
    sleep 1
    if kill -0 "$pid" &>/dev/null; then
      kill -9 "$pid" &>/dev/null
    fi
    rm -f "$PID_FILE"
    ok "服务已停止 (PID: $pid)"
  else
    # PID 文件不存在但进程可能残留
    local procs
    procs=$(pgrep -f "main.py" 2>/dev/null)
    if [[ -n "$procs" ]]; then
      echo "$procs" | xargs kill -9 &>/dev/null
      ok "清理残余进程: $procs"
    else
      warn "服务本来就未在运行。"
    fi
    rm -f "$PID_FILE"
  fi
}

# ────────────────────────────────────────────────────────────
# 状态检查
# ────────────────────────────────────────────────────────────
show_status() {
  echo ""
  echo -e "${W}═══ PDD AI 客服 — 服务状态 ══════════════════════${N}"
  echo ""

  # 进程
  if bot_alive; then
    echo -e "  ${G}●${N} 进程       [运行中]  PID: $(cat "$PID_FILE")"
  else
    echo -e "  ${R}○${N} 进程       [未运行]"
  fi

  # 端口
  if port_listening "$PORT"; then
    echo -e "  ${G}●${N} 端口 :${PORT}  [监听中]"
  else
    echo -e "  ${R}○${N} 端口 :${PORT}  [未监听]"
  fi

  # API 健康
  if api_healthy; then
    echo -e "  ${G}●${N} HTTP API   [健康 ✓]"
  elif port_listening "$PORT"; then
    echo -e "  ${Y}●${N} HTTP API   [端口在线但 API 无响应]"
  else
    echo -e "  ${R}○${N} HTTP API   [不可用]"
  fi

  echo ""
  echo -e "  ${W}访问地址:${N}"
  echo -e "    Swagger 文档  →  http://localhost:${PORT}/docs"
  echo -e "    管理后台      →  http://localhost:${PORT}/admin"
  echo -e "    实时日志      →  tail -f $LOG_FILE"
  echo ""
  echo -e "${W}════════════════════════════════════════════════${N}"
  echo ""
}

# ────────────────────────────────────────────────────────────
# 打开管理后台
# ────────────────────────────────────────────────────────────
open_admin() {
  if api_healthy; then
    ok "正在打开管理后台..."
    open "http://localhost:${PORT}/admin"
  else
    err "服务未运行，请先执行 ./launch.sh start"
  fi
}

# ────────────────────────────────────────────────────────────
# 主入口
# ────────────────────────────────────────────────────────────
case "${1:-start}" in
  start)
    banner
    start_bot
    show_status
    ;;
  stop)
    banner
    stop_bot
    ;;
  restart)
    banner
    stop_bot
    echo ""
    sleep 1
    start_bot
    show_status
    ;;
  status)
    show_status
    ;;
  admin)
    open_admin
    ;;
  log)
    log "实时日志（Ctrl+C 退出）："
    tail -f "$LOG_FILE"
    ;;
  log-tail)
    tail -50 "$LOG_FILE" 2>/dev/null || warn "日志文件不存在"
    ;;
  *)
    echo ""
    echo -e "  ${W}用法:${N} ./launch.sh {start|stop|restart|status|admin|log|log-tail}"
    echo ""
    echo "    start     启动服务"
    echo "    stop      停止服务"
    echo "    restart   重启服务"
    echo "    status    查看服务状态"
    echo "    admin     打开管理后台（浏览器）"
    echo "    log       实时日志流"
    echo "    log-tail  最近50行日志"
    echo ""
    exit 1
    ;;
esac
