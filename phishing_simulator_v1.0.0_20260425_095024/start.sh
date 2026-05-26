#!/bin/bash

# 钓鱼链接模拟平台 - 生产环境启动脚本
# 使用方法: ./start.sh

echo "=========================================="
echo "钓鱼链接模拟与安全意识演示平台"
echo "=========================================="

# 检查 Python 版本
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python 3.7+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"

# 检查依赖
echo ""
echo "📦 检查依赖..."
pip3 install -r requirements.txt > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ 依赖检查完成"
else
    echo "❌ 依赖安装失败"
    exit 1
fi

# 检查环境变量
if [ -z "$ADMIN_PASSWORD" ]; then
    echo ""
    echo "⚠️  警告: 未设置 ADMIN_PASSWORD 环境变量"
    echo "   将使用默认密码: admin123"
    echo "   强烈建议在生产环境中修改密码！"
    export ADMIN_PASSWORD="admin123"
fi

if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  警告: 未设置 SECRET_KEY 环境变量"
    echo "   将使用默认密钥（不安全）"
    export SECRET_KEY="production-secret-key-change-me"
fi

# 初始化数据库
echo ""
echo "🗄️  初始化数据库..."
python3 -c "from app import init_db; init_db()"

# 选择启动方式
echo ""
echo "请选择启动方式:"
echo "1. 开发模式（前台运行，适合测试）"
echo "2. 生产模式（使用 Gunicorn，后台运行）"
read -p "请输入选项 (1/2): " choice

case $choice in
    1)
        echo ""
        echo "🚀 以开发模式启动..."
        echo "访问地址: http://0.0.0.0:5000"
        echo "按 Ctrl+C 停止服务"
        echo ""
        python3 app.py
        ;;
    2)
        # 检查 Gunicorn
        if ! command -v gunicorn &> /dev/null; then
            echo ""
            echo "📦 安装 Gunicorn..."
            pip3 install gunicorn
        fi
        
        echo ""
        echo "🚀 以生产模式启动（Gunicorn）..."
        echo "工作进程数: 4"
        echo "绑定地址: 0.0.0.0:5000"
        echo ""
        
        # 后台运行
        nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app > app.log 2>&1 &
        PID=$!
        
        echo "✅ 服务已启动"
        echo "进程 ID: $PID"
        echo "日志文件: app.log"
        echo "访问地址: http://0.0.0.0:5000"
        echo ""
        echo "查看日志: tail -f app.log"
        echo "停止服务: kill $PID"
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "⚠️  免责声明: 本系统仅供安全教育和授权内部测试使用"
echo "   严禁任何非法用途!"
echo "=========================================="
