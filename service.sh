#!/bin/bash

# 2026 分数组合计算器 - 服务控制脚本
# 用法: ./service.sh start|stop|restart|status

APP_DIR="/home/axing/applyPaySum2026/AlipaySum2026"
PID_FILE="$APP_DIR/app.pid"
LOG_FILE="$APP_DIR/app.log"
PYTHON="$APP_DIR/venv/bin/python"
PORT=8026

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "服务已经在运行中 (PID: $PID)"
            return 1
        else
            rm -f "$PID_FILE"
        fi
    fi

    echo "正在启动服务..."
    cd "$APP_DIR"
    nohup $PYTHON -m uvicorn app:app --host 0.0.0.0 --port $PORT --workers 4 > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2

    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "✅ 服务启动成功 (PID: $(cat $PID_FILE))"
        echo "访问地址: http://9.135.93.249:$PORT"
    else
        echo "❌ 服务启动失败，请查看日志: $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "正在停止服务 (PID: $PID)..."
            kill $PID
            sleep 2
            # 如果还没停，强制杀
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID
            fi
            rm -f "$PID_FILE"
            echo "✅ 服务已停止"
        else
            echo "服务未在运行"
            rm -f "$PID_FILE"
        fi
    else
        echo "服务未在运行 (PID文件不存在)"
        # 尝试查找并杀掉残留进程
        PIDS=$(pgrep -f "uvicorn app:app.*$PORT")
        if [ -n "$PIDS" ]; then
            echo "发现残留进程，正在清理..."
            kill $PIDS 2>/dev/null
            echo "✅ 已清理"
        fi
    fi
}

restart() {
    echo "正在重启服务..."
    stop
    sleep 1
    start
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ 服务运行中 (PID: $PID)"
            echo "访问地址: http://9.135.93.249:$PORT"
            echo ""
            echo "--- 最近日志 ---"
            tail -5 "$LOG_FILE"
            return 0
        else
            echo "❌ 服务未运行 (PID文件存在但进程已死)"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo "❌ 服务未运行"
        return 1
    fi
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "日志文件不存在"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "  start   - 启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  status  - 查看状态"
        echo "  logs    - 查看实时日志"
        exit 1
        ;;
esac
