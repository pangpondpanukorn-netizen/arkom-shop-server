"""
===================================================================
 🔮 ARKOM SHOP - CLOUD SERVER API (RENDER BACKEND) 🔮
 ระบบหลังบ้านตรวจสอบสิทธิ์ + ระบบเก็บข้อมูลคีย์ + Log ภาษาไทย
===================================================================
"""

import datetime
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# 📌 ตัวแปรเก็บฐานข้อมูลคีย์จำลองบนเซิร์ฟเวอร์ (หน่วยความจำแรม)
db_storage = {}

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

    # ตรวจสอบว่ามีคีย์นี้อยู่ในฐานข้อมูลหรือไม่
    if user_key in db_storage:
        key_info = db_storage[user_key]
        
        # อัปเดตสถานะเป็น ACTIVE และบันทึก HWID/Discord หากยังไม่เคยใช้
        if key_info.get("status") == "UNUSED":
            key_info["status"] = "ACTIVE"
            key_info["hwid"] = hwid
            key_info["discord_id"] = discord_id

        server_log(
            action="🔑 ตรวจสอบสิทธิ์ (VALIDATE)", 
            status="✅ สำเร็จ (200)", 
            detail=f"Key: {user_key[:6]}... | Discord: {discord_id} | HWID: {hwid[:10]}..."
        )
        return jsonify({
            "success": True, 
            "message": "ยืนยันตัวตนสำเร็จ กำลังเข้าสู่ระบบ..."
        }), 200
    else:
        server_log(
            action="🔑 ตรวจสอบสิทธิ์ (VALIDATE)", 
            status="❌ ปฏิเสธการเข้าถึง (401)", 
            detail=f"ไม่พบคีย์ในระบบ: {user_key[:6]}... | IP: {client_ip}"
        )
        return jsonify({
            "success": False, 
            "message": "License Key ไม่ถูกต้องหรือไม่มีในระบบ"
        }), 400

# ---------------- API จัดการฐานข้อมูลคีย์ (เชื่อมต่อกับ Admin Panel) ----------------
@app.route('/api/db', methods=['GET', 'POST'])
def database_connection():
    global db_storage
    client_ip = request.remote_addr

    if request.method == 'POST':
        # รับข้อมูลฐานข้อมูลคีย์ใหม่จาก Admin Panel มาบันทึก
        new_db = request.json
        if isinstance(new_db, dict):
            db_storage = new_db
            server_log(
                action="🗄️ อัปเดตฐานข้อมูลคีย์ (SAVE DB)", 
                status="✅ สำเร็จ (200)", 
                detail=f"จำนวนคีย์ทั้งหมด: {len(db_storage)} ชุด | IP: {client_ip}"
            )
            return jsonify({"status": "success", "message": "Database saved successfully"}), 200
        else:
            server_log(
                action="🗄️ อัปเดตฐานข้อมูลคีย์ (SAVE DB)", 
                status="❌ ผิดพลาด (400)", 
                detail=f"รูปแบบข้อมูลไม่ถูกต้อง | IP: {client_ip}"
            )
            return jsonify({"status": "error", "message": "Invalid format"}), 400
            
    else:
        # ส่งข้อมูลฐานข้อมูลคีย์ทั้งหมดกลับไปแสดงผลที่ Admin Panel
        server_log(
            action="🗄️ ดึงข้อมูลฐานข้อมูล (GET DB)", 
            status="✅ สำเร็จ (200)", 
            detail=f"ส่งข้อมูลคีย์ {len(db_storage)} ชุด | IP: {client_ip}"
        )
        return jsonify(db_storage), 200

# ---------------- เริ่มต้นรันเซิร์ฟเวอร์ ----------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
