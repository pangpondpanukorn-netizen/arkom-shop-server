"""
===================================================================
 🔮 ARKOM SHOP - CLOUD SERVER API (RENDER + JSONBIN) 🔮
 ระบบหลังบ้านตรวจสอบสิทธิ์ + เซฟข้อมูลลง Cloud ถาวร + Log ภาษาไทย
===================================================================
"""

import datetime
import os
import time
import requests
from flask import Flask, jsonify, request
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

# ---------------- 📌 ตั้งค่าเชื่อมต่อ JSONBin.io ----------------
BIN_ID = "6ab37156ffd5d16053258be9"
MASTER_KEY = "$2a$10$Vua8.BJCLfyVI/7rVjCYEuc4UaMD7BAcYIyqglOT2vBsQCrJpEmpG"

JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": MASTER_KEY,
    "X-Bin-Versioning": "false"  # 👈 ปิด Versioning เพื่อให้เขียนบันทึกทับไฟล์เดิมได้ตลอด
}

# ---------------- ตั้งค่า Session + Retry ช่วยให้เชื่อมต่อเสถียรขึ้น ----------------
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# ---------------- ฟังก์ชันช่วยจัดการข้อมูล Cloud ----------------
def fetch_cloud_db():
    """ดึงข้อมูลคีย์ล่าสุดจาก JSONBin Cloud"""
    try:
        # 👈 ปรับ timeout เป็น 30 วินาที และใช้ session retry
        res = session.get(f"{JSONBIN_URL}/latest", headers=HEADERS, timeout=30)
        if res.status_code in [200, 201]:
            return res.json().get("record", {})
    except Exception as e:
        print(f"❌ Error fetching from JSONBin: {e}")
    return {}

def save_cloud_db(data):
    """บันทึกข้อมูลคีย์กลับไปยัง JSONBin Cloud"""
    try:
        # 👈 ปรับ timeout เป็น 30 วินาที และใช้ session retry
        res = session.put(JSONBIN_URL, json=data, headers=HEADERS, timeout=30)
        print(f"🔍 DEBUG Response: {res.status_code} | {res.text}")
        return res.status_code in [200, 201]
    except Exception as e:
        print(f"❌ Error saving to JSONBin: {e}")
        return False

# ---------------- ฟังก์ชันระบบ Log แบบอ่านง่าย ----------------
def server_log(action, status, detail=""):
    """
    จัดรูปแบบข้อความ Log ให้แสดงผลบน Render Dashboard แบบมีระเบียบ
    พร้อมระบุเวลา สถานะ และรายละเอียดของผู้ใช้งาน
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {action} --> สถานะ: {status} | {detail}")

@app.route('/')
@app.route('/api/health')
def index():
    server_log("🌐 เข้าชมหน้าแรก (HOME / HEALTH)", "✅ สำเร็จ (200)", f"IP: {request.remote_addr}")
    return "Arkom Shop Cloud Server is Online and Running! 🚀"

# ---------------- API ตรวจสอบสิทธิ์ License Key ----------------
@app.route('/api/validate', methods=['POST'])
def validate_license():
    data = request.json or {}
    user_key = data.get("key", "").strip()
    hwid = data.get("hwid", "").strip()
    discord_id = data.get("discord_id", "").strip()
    client_ip = request.remote_addr

    if not user_key or not hwid:
        return jsonify({"success": False, "message": "ข้อมูลไม่ถูกต้อง"}), 400

    # ดึงข้อมูลล่าสุดจาก Cloud
    db_storage = fetch_cloud_db()

    # ตรวจสอบว่ามีคีย์นี้อยู่ในฐานข้อมูลหรือไม่
    if user_key in db_storage:
        key_info = db_storage[user_key]
        now = time.time()

        # 1. ตรวจสอบวันหมดอายุ (ถ้ามีกำหนดไว้)
        expire_at = key_info.get("expire_at", -1)
        if expire_at != -1 and now > expire_at:
            server_log(
                action="🔑 ตรวจสอบสิทธิ์ (VALIDATE)", 
                status="❌ หมดอายุ (400)", 
                detail=f"Key: {user_key[:6]}... | หมดอายุแล้ว"
            )
            return jsonify({"success": False, "message": "License Key นี้หมดอายุการใช้งานแล้ว"}), 400

        saved_hwid = key_info.get("hwid")

        # 2. ผูก HWID เมื่อใช้งานครั้งแรก
        if key_info.get("status") == "UNUSED" or not saved_hwid:
            key_info["status"] = "ACTIVE"
            key_info["hwid"] = hwid
            key_info["discord_id"] = discord_id
            
            db_storage[user_key] = key_info
            save_cloud_db(db_storage) # บันทึก HWID ลง Cloud ทันที

            server_log(
                action="🔑 ลงทะเบียนเครื่องแรก (ACTIVATE)", 
                status="✅ สำเร็จ (200)", 
                detail=f"Key: {user_key[:6]}... | Discord: {discord_id} | HWID: {hwid[:10]}..."
            )
            return jsonify({
                "success": True, 
                "message": "ลงทะเบียนเครื่องและเข้าสู่ระบบสำเร็จ!"
            }), 200

        # 3. ตรวจสอบการย้ายเครื่อง (HWID ไม่ตรง)
        if saved_hwid != hwid:
            server_log(
                action="🔑 ตรวจสอบสิทธิ์ (VALIDATE)", 
                status="❌ เครื่องไม่ตรง (400)", 
                detail=f"Key: {user_key[:6]}... | HWID ไม่ตรงกับในระบบ"
            )
            return jsonify({
                "success": False, 
                "message": "License Key ถูกใช้งานกับเครื่องอื่นอยู่แล้ว"
            }), 400

        # 4. ยืนยันสิทธิ์สำเร็จ
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
    client_ip = request.remote_addr

    if request.method == 'POST':
        # รับข้อมูลฐานข้อมูลคีย์ใหม่จาก Admin Panel มาบันทึกลง Cloud
        new_db = request.json
        if isinstance(new_db, dict):
            if save_cloud_db(new_db):
                server_log(
                    action="🗄️ อัปเดตฐานข้อมูลคีย์ (SAVE DB)", 
                    status="✅ สำเร็จ (200)", 
                    detail=f"จำนวนคีย์ทั้งหมด: {len(new_db)} ชุด | IP: {client_ip}"
                )
                return jsonify({"status": "success", "message": "Database saved successfully"}), 200
            else:
                return jsonify({"status": "error", "message": "Failed to save to Cloud"}), 500
        else:
            server_log(
                action="🗄️ อัปเดตฐานข้อมูลคีย์ (SAVE DB)", 
                status="❌ ผิดพลาด (400)", 
                detail=f"รูปแบบข้อมูลไม่ถูกต้อง | IP: {client_ip}"
            )
            return jsonify({"status": "error", "message": "Invalid format"}), 400
            
    else:
        # ดึงข้อมูลจาก Cloud ส่งกลับไปแสดงผลที่ Admin Panel
        db_storage = fetch_cloud_db()
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
