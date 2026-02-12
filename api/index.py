from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import os

app = Flask(__name__)
# Vercel-এ যাতে ফ্রন্টএন্ড থেকে রিকোয়েস্ট ব্লক না হয়, তাই CORS অন করা হলো
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ---------------------------------------------------------
# 1. SUPABASE CONNECTION CONFIGURATION
# ---------------------------------------------------------
# Vercel Environment Variables থেকে URL এবং KEY নিবে
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = None

if url and key:
    supabase = create_client(url, key)
else:
    print("Warning: Supabase credentials missing!")

# ---------------------------------------------------------
# 2. HELPER: AUTH CHECK
# ---------------------------------------------------------
def get_user_id(req):
    """
    Request Header থেকে টোকেন নিয়ে ইউজার ভেরিফাই করে ID রিটার্ন করে।
    """
    token = req.headers.get("Authorization")
    if not token:
        return None
    try:
        # "Bearer <token>" থেকে শুধু টোকেনটা আলাদা করা
        jwt = token.replace("Bearer ", "")
        user = supabase.auth.get_user(jwt)
        return user.user.id
    except:
        return None

# ---------------------------------------------------------
# 3. ROUTE: SYSTEM STATUS (The Gatekeeper)
# ---------------------------------------------------------
@app.route('/api/system-status', methods=['GET'])
def system_status():
    """
    ফ্রন্টএন্ড লোড হওয়ার সাথে সাথে এই API কল হবে।
    এটি ডিসিশন নিবে ইউজার ড্যাশবোর্ড দেখবে নাকি মেইনটেনেন্স পেজ।
    """
    if not supabase:
        return jsonify({"error": "Database Config Error"}), 500

    try:
        # 1. গ্লোবাল সেটিংস চেক (ID=1)
        settings_res = supabase.table('system_settings').select("*").eq('id', 1).single().execute()
        settings = settings_res.data

        # 2. যদি মেইনটেনেন্স মোড অন থাকে
        if settings.get('is_maintenance_mode'):
            return jsonify({
                "action": "maintenance",
                "message": settings.get('notice_text')
            }), 503

        # 3. ইউজার লগিন করা থাকলে তার স্ট্যাটাস চেক
        user_id = get_user_id(request)
        user_status = "guest"
        
        if user_id:
            profile_res = supabase.table('profiles').select("*").eq('id', user_id).single().execute()
            profile = profile_res.data
            
            if profile:
                # যদি অ্যাক্টিভেশন ফি অন থাকে এবং ইউজারের একাউন্ট একটিভ না হয়
                if settings.get('is_activation_required') and not profile.get('is_active'):
                    # এডমিন হলে মাফ
                    if profile.get('role') != 'admin':
                        return jsonify({
                            "action": "activation_required",
                            "fee": settings.get('activation_fee'),
                            "bkash": settings.get('bkash_number'),
                            "nagad": settings.get('nagad_number')
                        }), 200
                
                user_status = "active"

        # সব ঠিক থাকলে ড্যাশবোর্ড এক্সেস
        return jsonify({
            "action": "operational",
            "user_status": user_status,
            "settings": settings
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------
# 4. ROUTE: SUBMIT ACTIVATION PAYMENT
# ---------------------------------------------------------
@app.route('/api/submit-activation', methods=['POST'])
def submit_activation():
    user_id = get_user_id(request)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    
    try:
        # পেমেন্ট রিকোয়েস্ট ডাটাবেসে সেভ করা
        new_request = {
            "user_id": user_id,
            "payment_method": data.get('method'), # bKash / Nagad
            "sender_number": data.get('sender_number'),
            "transaction_id": data.get('transaction_id'),
            "amount": data.get('amount'),
            "status": "pending"
        }
        
        supabase.table('activation_requests').insert(new_request).execute()
        
        return jsonify({"message": "Payment submitted! Please wait for admin approval."}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---------------------------------------------------------
# 5. HEALTH CHECK (For Vercel)
# ---------------------------------------------------------
@app.route('/api/health')
def health():
    return jsonify({"status": "TaskKing Backend Running 🚀"})

# Vercel-এর জন্য app.run() দরকার নেই, তবে লোকাল টেস্টের জন্য রাখা হলো
if __name__ == '__main__':
    app.run(debug=True, port=5328)
