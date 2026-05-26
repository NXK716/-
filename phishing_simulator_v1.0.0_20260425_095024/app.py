import os
import uuid
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from user_agents import parse as ua_parse
import requests

# 加载环境变量（如果存在 .env 文件）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv 未安装，使用系统环境变量

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

DATABASE = 'phishing_simulator.db'

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 创建 links 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_id TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建 visits 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip TEXT,
            user_agent TEXT,
            device_type TEXT,
            os TEXT,
            browser TEXT,
            geo_location TEXT,
            FOREIGN KEY (link_id) REFERENCES links(unique_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_geo_location(ip):
    """通过免费 API 获取 IP 地理位置"""
    try:
        if ip in ['127.0.0.1', '::1', 'localhost']:
            return "本地地址"
        
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                city = data.get('city', '未知')
                country = data.get('country', '未知')
                return f"{city}, {country}"
        return "位置获取失败"
    except Exception as e:
        print(f"地理位置查询失败: {e}")
        return "位置获取失败"

@app.route('/')
def index():
    """首页重定向到管理员登录"""
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录页面"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin.html', error='密码错误', login_mode=True)
    return render_template('admin.html', login_mode=True)

@app.route('/admin')
def admin_panel():
    """管理员面板"""
    if not session.get('authenticated'):
        return redirect(url_for('admin_login'))
    return render_template('admin.html', login_mode=False)

@app.route('/api/generate_link', methods=['POST'])
def generate_link():
    """生成钓鱼链接"""
    if not session.get('authenticated'):
        return jsonify({'error': '未授权'}), 401
    
    unique_id = str(uuid.uuid4())
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO links (unique_id) VALUES (?)', (unique_id,))
    conn.commit()
    conn.close()
    
    base_url = request.host_url.rstrip('/')
    full_url = f"{base_url}/track/{unique_id}"
    
    return jsonify({
        'success': True,
        'unique_id': unique_id,
        'url': full_url
    })

@app.route('/api/visits')
def get_visits():
    """获取所有访问记录"""
    if not session.get('authenticated'):
        return jsonify({'error': '未授权'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT v.*, l.unique_id as link_unique_id 
        FROM visits v 
        JOIN links l ON v.link_id = l.unique_id 
        ORDER BY v.timestamp DESC
    ''')
    visits = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(visits)

@app.route('/track/<unique_id>')
def track_visit(unique_id):
    """钓鱼链接跟踪页面"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 验证链接是否存在
    cursor.execute('SELECT id FROM links WHERE unique_id = ?', (unique_id,))
    link = cursor.fetchone()
    
    if not link:
        conn.close()
        return render_template('warning.html', error='无效链接'), 404
    
    # 获取客户端信息
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    
    user_agent_string = request.headers.get('User-Agent', 'Unknown')
    
    # 解析 User-Agent
    ua = ua_parse(user_agent_string)
    device_type = '电脑'
    if ua.is_mobile:
        device_type = '手机'
    elif ua.is_tablet:
        device_type = '平板'
    
    os_info = f"{ua.os.family} {ua.os.version_string}".strip()
    browser_info = f"{ua.browser.family} {ua.browser.version_string}".strip()
    
    # 获取地理位置
    geo_location = get_geo_location(ip)
    
    # 记录访问
    cursor.execute('''
        INSERT INTO visits (link_id, ip, user_agent, device_type, os, browser, geo_location)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (unique_id, ip, user_agent_string, device_type, os_info, browser_info, geo_location))
    conn.commit()
    conn.close()
    
    # 渲染警告页面
    visit_info = {
        'ip': ip,
        'geo_location': geo_location,
        'device_type': device_type,
        'os': os_info,
        'browser': browser_info,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return render_template('warning.html', visit_info=visit_info, error=None)

if __name__ == '__main__':
    init_db()
    print("=" * 60)
    print("钓鱼链接模拟与安全意识演示平台")
    print("=" * 60)
    print("⚠️  免责声明:本系统仅供安全教育和授权内部测试使用")
    print("   严禁任何非法用途!")
    print("=" * 60)
    print(f"管理员入口: http://127.0.0.1:5000/admin")
    print(f"默认密码: {ADMIN_PASSWORD}")
    print("=" * 60)
    app.run(debug=False, host='0.0.0.0', port=5000)
