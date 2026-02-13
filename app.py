import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-change-this")

# -------------------------------------------------------------------
# 1. DATABASE CONNECTION (Supabase)
# -------------------------------------------------------------------
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase URL and Key must be set in .env or Vercel Environment Variables")

supabase: Client = create_client(url, key)

# -------------------------------------------------------------------
# 2. MIDDLEWARE (The "Brain" that checks rules before every page load)
# -------------------------------------------------------------------
@app.before_request
def before_request_checks():
    """
    This function runs before EVERY request.
    It checks:
    1. Is the site in Maintenance Mode?
    2. Is the user logged in?
    3. Does the user need to pay (Activation)?
    """
    
    # A. Load Site Settings (Global)
    try:
        response = supabase.table('site_settings').select('*').eq('id', 1).single().execute()
        g.settings = response.data
    except:
        # Default fallback if DB fails
        g.settings = {'maintenance_mode': False, 'activation_required': False, 'notice_text': ''}

    # B. Load User (If logged in)
    g.user = None
    if 'user_id' in session:
        try:
            user_resp = supabase.table('profiles').select('*').eq('id', session['user_id']).single().execute()
            g.user = user_resp.data
        except:
            session.clear() # Invalid session

    # C. CHECK: Maintenance Mode
    # If Mode is ON, and User is NOT Admin -> Show Maintenance Page
    if g.settings.get('maintenance_mode'):
        # Allow static files (css/js) and login page
        if request.endpoint in ['static', 'login', 'logout', 'admin_login']:
            return
        
        # If user is admin, let them pass
        if g.user and g.user.get('role') == 'admin':
            return
            
        return render_template('maintenance.html')

    # D. CHECK: Activation (Pay to Earn)
    # If Activation ON, User Logged In, User Not Active, Not Admin -> Redirect
    if g.settings.get('activation_required'):
        if g.user and not g.user.get('is_active') and g.user.get('role') != 'admin':
            allowed_routes = ['static', 'logout', 'activate_account', 'submit_activation']
            if request.endpoint not in allowed_routes:
                return redirect(url_for('activate_account'))

# -------------------------------------------------------------------
# 3. HELPER DECORATORS (Security)
# -------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or g.user.get('role') != 'admin':
            flash("⚠️ শুধুমাত্র এডমিন প্রবেশ করতে পারবে।", "error")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------------------------------------
# 4. ROUTES (Pages)
# -------------------------------------------------------------------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# --- AUTH SYSTEM ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Sign in with Supabase Auth
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            session['user_id'] = res.user.id
            session['access_token'] = res.session.access_token
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash("❌ ইমেইল বা পাসওয়ার্ড ভুল হয়েছে।", "error")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Create user in Supabase
            res = supabase.auth.sign_up({"email": email, "password": password})
            flash("✅ একাউন্ট তৈরি হয়েছে! লগিন করুন।", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash("❌ রেজিস্ট্রেশন ব্যর্থ হয়েছে। অন্য ইমেইল ব্যবহার করুন।", "error")
            return redirect(url_for('register'))
            
    return render_template('register.html') # এই লাইনটি চেক করুন
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- USER DASHBOARD ---
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html', user=g.user, settings=g.settings)

@app.route('/tasks')
@login_required
def tasks():
    # Fetch active tasks from DB
    response = supabase.table('tasks').select('*').eq('is_active', True).execute()
    return render_template('tasks.html', tasks=response.data, user=g.user)

# --- ACTIVATION SYSTEM ---
@app.route('/activate')
@login_required
def activate_account():
    return render_template('activation.html', user=g.user)

@app.route('/activate/submit', methods=['POST'])
@login_required
def submit_activation():
    trx_id = request.form.get('trx_id')
    method = request.form.get('method')
    
    # Save request to DB (You need a 'activations' table or update profile)
    # For now, we just flash a message
    flash("✅ রিকোয়েস্ট জমা হয়েছে। এডমিন চেক করে এপ্রুভ করবেন।", "success")
    return redirect(url_for('activate_account'))

# -------------------------------------------------------------------
# 5. ADMIN PANEL (The Control Room)
# -------------------------------------------------------------------
# --- ADMIN PANEL ROUTE ---
@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_panel():
    # ১. সেটিংস আপডেট লজিক (POST Request)
    if request.method == 'POST':
        # HTML ফর্ম থেকে ডাটা নেওয়া
        m_mode = True if request.form.get('maintenance') == 'on' else False
        a_req = True if request.form.get('activation') == 'on' else False
        notice = request.form.get('notice')

        try:
            # Supabase-এ আপডেট করা
            supabase.table('site_settings').update({
                'maintenance_mode': m_mode,
                'activation_required': a_req,
                'notice_text': notice
            }).eq('id', 1).execute()

            flash("✅ সেটিংস সফলভাবে সেভ হয়েছে!", "success")
            
            # নতুন সেটিংস লোড করার জন্য পেজ রিফ্রেশ
            return redirect(url_for('admin_panel'))
            
        except Exception as e:
            flash(f"Error: {str(e)}", "error")

    # ২. পেজ লোড করার সময় বর্তমান সেটিংস দেখানো (GET Request)
    # g.settings এবং g.user অটোমেটিক লোড হয় (before_request এর মাধ্যমে)
    
    # টোটাল ইউজার কাউন্ট (অপশনাল - ড্যাশবোর্ডে দেখানোর জন্য)
    try:
        user_count = supabase.table('profiles').select('*', count='exact').execute().count
    except:
        user_count = 0

    return render_template('admin.html', user=g.user, settings=g.settings, user_count=user_count)
# --- VERCEL ENTRY POINT ---
# This is required for local testing, Vercel ignores it but uses the 'app' object
if __name__ == '__main__':
    app.run(debug=True)
