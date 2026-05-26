@echo off
chcp 65001 >nul
REM 钓鱼链接模拟平台 - Windows 启动脚本

echo ==========================================
echo 钓鱼链接模拟与安全意识演示平台
echo ==========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python，请先安装 Python 3.7+
    pause
    exit /b 1
)

echo ✅ Python 已安装
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo %PYTHON_VERSION%
echo.

REM 检查依赖
echo 📦 检查依赖...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✅ 依赖检查完成
echo.

REM 检查环境变量
if "%ADMIN_PASSWORD%"=="" (
    echo ⚠️  警告: 未设置 ADMIN_PASSWORD 环境变量
    echo    将使用默认密码: admin123
    echo    强烈建议在生产环境中修改密码！
    set ADMIN_PASSWORD=admin123
)

if "%SECRET_KEY%"=="" (
    echo ⚠️  警告: 未设置 SECRET_KEY 环境变量
    echo    将使用默认密钥（不安全）
    set SECRET_KEY=production-secret-key-change-me
)

REM 初始化数据库
echo 🗄️  初始化数据库...
python -c "from app import init_db; init_db()"
echo.

REM 选择启动方式
echo 请选择启动方式:
echo 1. 开发模式（前台运行，适合测试）
echo 2. 生产模式（使用 Waitress，后台运行）
set /p choice="请输入选项 (1/2): "

if "%choice%"=="1" goto dev_mode
if "%choice%"=="2" goto prod_mode
echo ❌ 无效选项
pause
exit /b 1

:dev_mode
echo.
echo 🚀 以开发模式启动...
echo 访问地址: http://0.0.0.0:5000
echo 按 Ctrl+C 停止服务
echo.
python app.py
goto end

:prod_mode
REM 检查 Waitress
pip show waitress >nul 2>&1
if errorlevel 1 (
    echo.
    echo 📦 安装 Waitress...
    pip install waitress
)

echo.
echo 🚀 以生产模式启动（Waitress）...
echo 绑定地址: 0.0.0.0:5000
echo.

start "Phishing Simulator" python -m waitress.serve --host=0.0.0.0 --port=5000 app:app

echo ✅ 服务已在后台启动
echo 访问地址: http://0.0.0.0:5000
echo.
echo 停止服务: 关闭命令行窗口或任务管理器结束进程
goto end

:end
echo.
echo ==========================================
echo ⚠️  免责声明: 本系统仅供安全教育和授权内部测试使用
echo    严禁任何非法用途!
echo ==========================================
pause
