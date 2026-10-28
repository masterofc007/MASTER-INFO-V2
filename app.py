import time
import httpx
import json
import sys
from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from google.protobuf import json_format

try:
    import main_pb2, AccountPersonalShow_pb2
    print("Proto files imported")
except ImportError as e:
    print(f"Proto import error: {e}")
    sys.exit(1)

USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 14; CPH2095 Build/RKQ1.211119.001)"
MAIN_KEY = b'Yg&tc%DEuh6%Zc^8'
MAIN_IV = b'6oyZDr22E3ychjM%'

JWT_API_BASE = "https://jwt-apis-ob55.onrender.com/token"

# ═══════════════════════════════════════════
#  APNA ACCOUNT YAHAN DAAL
# ═══════════════════════════════════════════
ACC_UID = "8086782640"
ACC_PW  = "D9C774CBE52BDEC71C5D253F5E0D8D787232F6D65462DB2BCE20E2F1D22899AE"

SERVER_URL = "https://client.ind.freefiremobile.com"
RELEASE = "OB55"

REGION_NAME_TO_CODE = {
    "IND": "1", "SG": "2", "BR": "3", "RU": "4", "ID": "5",
    "TW": "6", "US": "7", "VN": "8", "TH": "9", "ME": "10", "BD": "13",
}

app = Flask(__name__)
_tk = {"tk": None, "exp": 0}

def aes_enc(p):
    pl = AES.block_size - (len(p) % AES.block_size)
    return AES.new(MAIN_KEY, AES.MODE_CBC, MAIN_IV).encrypt(p + bytes([pl] * pl))

def get_token():
    now = time.time()
    if _tk["tk"] and _tk["exp"] > now:
        return _tk["tk"]
    try:
        r = httpx.get(f"{JWT_API_BASE}?uid={ACC_UID}&password={ACC_PW}&api_key=JWT_API_KEY", timeout=15)
        print(f"[JWT] {r.status_code}")
        d = r.json()
        tk = d.get("token")
        if tk:
            _tk["tk"] = tk
            _tk["exp"] = now + 14400
            print("[JWT OK]")
            return tk
        print(f"[JWT FAIL] {d}")
    except Exception as e:
        print(f"[JWT ERR] {e}")
    return None

@app.route("/info")
def info():
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "UID required"}), 400
    try:
        uid_int = int(uid)
    except:
        return jsonify({"error": "Invalid UID"}), 400

    tk = get_token()
    if not tk:
        return jsonify({"error": "No token"}), 500

    req = main_pb2.GetPlayerPersonalShow()
    req.a = uid_int
    req.b = 7
    h = {
        "User-Agent": USERAGENT,
        "Connection": "Keep-Alive",
        "Content-Type": "application/octet-stream",
        "Authorization": f"Bearer {tk}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": RELEASE,
    }
    try:
        r = httpx.post(f"{SERVER_URL}/GetPlayerPersonalShow",
                       data=aes_enc(req.SerializeToString()),
                       headers=h, timeout=15)
        print(f"[GARENA] {r.status_code} len={len(r.content)}")
        if r.status_code != 200:
            return jsonify({"error": f"Garena {r.status_code}"}), r.status_code

        obj = AccountPersonalShow_pb2.AccountPersonalShowInfo()
        obj.ParseFromString(r.content)
        raw = json.loads(json_format.MessageToJson(obj, preserving_proto_field_name=True))

        basic = raw.get("basic_info", {}) or {}
        nickname = basic.get("nickname", "Unknown")
        
        # 🚀 YAHAN FIX HAI: Unicode kachre ko theek karne ke liye
        if nickname and "\\u" in str(nickname):
            try:
                nickname = nickname.encode('latin-1').decode('utf-8')
            except:
                pass

        level = basic.get("level", 0)
        likes = basic.get("liked", 0)
        region_name = basic.get("region", "IND")
        region_code = REGION_NAME_TO_CODE.get(region_name, "1")

        account_info = {
            "AccountName": nickname,
            "AccountLevel": level,
            "AccountLikes": likes,
            "AccountRegion": region_code,
            "AccountUID": uid,
        }

        return jsonify({
            "status": 1,
            "credit": "@Master_ff_01",
            "channel": "@Masterofficialchannel",
            "AccountInfo": account_info,
            "accountInfo": account_info,
            "basic_info": {
                "nickname": nickname,
                "level": level,
                "liked": likes,
                "region": region_name,
                "account_id": uid,
            },
            "data": raw,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset-cache")
def reset_cache():
    _tk["tk"] = None
    _tk["exp"] = 0
    return jsonify({"message": "cleared", "credit": "@Master_ff_01"})

@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "endpoint": "/info?uid=XXX",
        "credit": "@Master_ff_01",
    })

handler = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
