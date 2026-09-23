from flask import Flask, request, jsonify
import json
import os
import time

app = Flask(__name__)
KEYS_DB_FILE = "keys_db.json"

def load_db():
    if not os.path.exists(KEYS_DB_FILE):
        return {}
    try:
        with open(KEYS_DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        
        # ระบบลบคีย์หมดอายุอัตโนมัติบนเซิร์ฟเวอร์
        now = time.time()
        expired_keys = [k for k, info in db.items() if info.get("expire_at", -1) != -1 and now > info.get("expire_at", -1)]
        if expired_keys:
            for k in expired_keys:
                del db[k]
            save_db(db)
        return db
    except Exception:
        return {}

def save_db(db):
    with open(KEYS_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

# Endpoint สำหรับให้ Admin ดึงและบันทึกข้อมูลฐานข้อมูลคีย์
@app.route("/api/db", methods=["GET", "POST"])
def handle_db():
    if request.method == "GET":
        return jsonify(load_db())
    elif request.method == "POST":
        data = request.json
        if data is not None:
            save_db(data)
            return jsonify({"success": True, "message": "บันทึกข้อมูลสำเร็จ"})
        return jsonify({"success": False, "message": "ข้อมูลไม่ถูกต้อง"}), 400

# Endpoint สำหรับให้ Client ตรวจสอบสิทธิ์และผูก HWID
@app.route("/api/validate", methods=["POST"])
def validate_key():
    req = request.json
    key_str = req.get("key")
    discord_id = req.get("discord_id")
    hwid = req.get("hwid")

    db = load_db()
    if key_str not in db:
        return jsonify({"success": False, "message": "ไม่พบรหัสสิทธิ์การใช้งานนี้ในระบบ"})

    kdata = db[key_str]
    now = time.time()

    if kdata["expire_at"] != -1 and now > kdata["expire_at"]:
        return jsonify({"success": False, "message": "สิทธิ์การใช้งานนี้หมดอายุลงแล้ว"})

    if kdata["status"] == "UNUSED":
        kdata["status"] = "ACTIVE"
        kdata["used_at"] = now
        kdata["hwid"] = hwid
        kdata["discord_id"] = discord_id
        db[key_str] = kdata
        save_db(db)
        return jsonify({"success": True, "message": "เปิดใช้งานสิทธิ์ครั้งแรกสำเร็จ! ผูกกับอุปกรณ์และ Discord เรียบร้อย"})

    if kdata["status"] == "ACTIVE":
        if kdata["hwid"] != hwid:
            return jsonify({"success": False, "message": "การเข้าถึงถูกปฏิเสธ: ฮาร์ดแวร์ (HWID) ไม่ตรงกับเครื่องที่ลงทะเบียนไว้"})
        if kdata.get("discord_id") and kdata.get("discord_id") != discord_id:
            return jsonify({"success": False, "message": "การเข้าถึงถูกปฏิเสธ: Discord ID ไม่ตรงกับข้อมูลเดิม"})
        return jsonify({"success": True, "message": "ยืนยันตัวตนสำเร็จ กำลังเข้าสู่ระบบ..."})

    return jsonify({"success": False, "message": "สิทธิ์การใช้งานนี้ถูกระงับชั่วคราว"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)