"""
===================================================================
 🔮 ARKOM SHOP - CLOUD SERVER API (RENDER BACKEND) 🔮
 ระบบหลังบ้านตรวจสอบสิทธิ์ พร้อมระบบ Log ภาษาไทยอ่านง่าย
===================================================================
"""

import datetime
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# ---------------- ฟังก์ชันระบบ Log แบบอ่านง่าย ----------------
def server_log(action, status, detail=""):
    """
    จัดรูปแบบข้อความ Log ให้แสดงผลบน Render Dashboard แบบมีระเบียบ
    พร้อมระบุเวลา สถานะ และรายละเอียดของผู้ใช้งาน
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {action} --> สถานะ: {status} | {detail}")

@app.route('/')
def index():
    server_log("🌐 เข้าชมหน้าแรก (HOME)", "✅ สำเร็จ (200)", f"IP: {request.remote_addr}")
    return "Arkom Shop Cloud Server is Online and Running! 🚀"

# ---------------- API ตรวจสอบสิทธิ์ License Key ----------------
@app.route('/api/validate', methods=['POST'])
def validate_license():
    data = request.json or {}
    user_key = data.get("key", "").strip()
    hwid = data.get("hwid", "").strip()
    discord_id = data.get("discord_id", "").strip()
    client_ip = request.remote_addr

    # 📌 จุดเชื่อมต่อฐานข้อมูล (Database Validation)
    # สามารถเขียนโค้ดเชื่อมต่อฐานข้อมูลจริงของคุณตรงนี้ได้เลย
    # ตัวอย่างจำลอง: กำหนดให้คีย์ผ่านเสมอหากกรอกข้อมูลมา
    is_key_valid = True  
    
    if is_key_valid:
        # บันทึก Log เมื่อตรวจสอบสิทธิ์ผ่าน
        server_log(
            action="🔑 ตรวจสอบสิทธิ์ (VALIDATE)", 
            status="✅ สำเร็จ (200)", 
            detail=f"Discord ID: {discord_id} | HWID: {hwid[:10]}... | IP: {client_ip}"
        )
        return jsonify({
            "success": True, 
            "message": "ยืนยันตัวตนสำเร็จ กำลังเข้าสู่ระบบ..."
        }), 200
    else:
        # บันทึก Log เมื่อคีย์ไม่ถูกต้องหรือถูกปฏิเสธ
        server_log(
            action="🔑 ตรวจสอบสิทธิ์ (VALIDATE)", 
            status="❌ ปฏิเสธการเข้าถึง (401)", 
            detail=f"Key: {user_key[:6]}... | Discord ID: {discord_id} | IP: {client_ip}"
        )
        return jsonify({
            "success": False, 
            "message": "License Key ไม่ถูกต้องหรือหมดอายุ"
        }), 400

# ---------------- API เรียกข้อมูลฐานข้อมูลระบบ ----------------
@app.route('/api/db', methods=['GET', 'POST'])
def database_connection():
    client_ip = request.remote_addr
    server_log(
        action="🗄️ เรียกข้อมูลฐานข้อมูล (DATABASE)", 
        status="✅ สำเร็จ (200)", 
        detail=f"Request จาก IP: {client_ip}"
    )
    return jsonify({
        "status": "connected", 
        "message": "Database ready & synchronized"
    }), 200

# ---------------- เริ่มต้นรันเซิร์ฟเวอร์ ----------------
if __name__ == '__main__':
    # ดึงพอร์ตจาก Environment ของ Render หรือใช้พอร์ต 10000 เป็นค่าเริ่มต้น
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    app.run(host="0.0.0.0", port=5000)
