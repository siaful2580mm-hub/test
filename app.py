import os
import random
import string
import requests
import base64
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
# 2. MIDDLEWARE (Updated Logic)
# -------------------------------------------------------------------
@app.before_request
def before_request_checks():
    """
    This function runs before EVERY request.
    It checks Maintenance, Login, and Activation status.
    """
    
    # A. Load Site Settings (Global)
    try:
        response = supabase.table('site_settings').select('*').eq('id', 1).single().execute()
        g.settings = response.data
    except:
        g.settings = {'maintenance_mode': False, 'activation_required': False, 'notice_text': ''}

    # B. Load User (If logged in)
    g.user = None
    if 'user_id' in session:
        try:
            user_resp = supabase.table('profiles').select('*').eq('id', session['user_id']).single().execute()
            g.user = user_resp.data
        except:
            session.clear()

    # C. CHECK: Maintenance Mode
    if g.settings.get('maintenance_mode'):
        if request.endpoint in ['static', 'login', 'logout', 'admin_login']:
            return
        if g.user and g.user.get('role') == 'admin':
            return
        return render_template('maintenance.html')

    # D. CHECK: Activation (Pay to Earn) - [UPDATED HERE]
    # লজিক: ড্যাশবোর্ড দেখা যাবে, কিন্তু 'tasks' পেজে গেলে আটকাবে।
    if g.settings.get('activation_required'):
        if g.user and not g.user.get('is_active') and g.user.get('role') != 'admin':
            
            # ১. যদি ইউজার 'tasks' পেজে যেতে চায় -> তাকে আটকাও
            if request.endpoint == 'tasks':
                flash("⚠️ কাজ করার জন্য একাউন্ট ভেরিফাই করুন!", "error")
                return redirect(url_for('activate_account'))
            
            # ২. এই পেজগুলোতে সবাই ঢুকতে পারবে (Verified না হলেও)
            # dashboard এবং index এখানে যুক্ত আছে, তাই প্রোফাইল দেখা যাবে।
            allowed_routes = ['static', 'logout', 'activate_account', 'submit_activation', 'dashboard', 'index', 'admin_panel']
            
            # ৩. যদি কেউ allowed লিস্টের বাইরের পেজে (যেমন hidden link) যেতে চায় -> আটকাও
            if request.endpoint and request.endpoint not in allowed_routes:
                 return redirect(url_for('activate_account'))

# -------------------------------------------------------------------
# 3. HELPER DECORATORS
# -------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- HELPER: UNIQUE CODE GENERATOR ---
def generate_ref_code():
    # TK + 4 Random Digits/Letters (Example: TK4A2B)
    chars = string.ascii_uppercase + string.digits
    code = 'TK' + ''.join(random.choices(chars, k=4))
    return code
    
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or g.user.get('role') != 'admin':
            flash("⚠️ শুধুমাত্র এডমিন প্রবেশ করতে পারবে।", "error")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------------------------------------
# 4. ROUTES
# -------------------------------------------------------------------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# --- ADMIN: ADD TASK (Fb Page Like / Screenshot Task) ---
@app.route('/adtask', methods=['GET', 'POST'])
@login_required
@admin_required
def add_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        link = request.form.get('link')
        reward = float(request.form.get('reward'))
        category = request.form.get('category') # Facebook, YouTube
        task_type = request.form.get('task_type') # 'screenshot' or 'link'
        
        try:
            supabase.table('tasks').insert({
                'title': title,
                'description': description,
                'link': link,
                'reward': reward,
                'category': category,
                'task_type': task_type,
                'is_active': True
            }).execute()
            flash("✅ টাস্ক সফলভাবে যোগ করা হয়েছে!", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            
        return redirect(url_for('add_task'))
        
    return render_template('adtask.html', user=g.user)

# --- USER: SUBMIT TASK (ImgBB Upload) ---
@app.route('/task/submit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def submit_task(task_id):
    # টাস্ক ডিটেইলস আনা
    task_res = supabase.table('tasks').select('*').eq('id', task_id).single().execute()
    task = task_res.data

    if request.method == 'POST':
        # ১. ছবি ফাইল ধরা
        if 'screenshot' not in request.files:
            flash("ছবি আপলোড করুন!", "error")
            return redirect(request.url)
            
        file = request.files['screenshot']
        if file.filename == '':
            flash("কোনো ছবি সিলেক্ট করা হয়নি", "error")
            return redirect(request.url)

        try:
            # ২. ImgBB তে আপলোড করা
            api_key = "f5789c14135a479b4e3893c6b9ccf074" # আপনার দেওয়া কী
            image_string = base64.b64encode(file.read())
            
            payload = {
                "key": api_key,
                "image": image_string,
            }
            
            # ImgBB API কল
            response = requests.post("https://api.imgbb.com/1/upload", data=payload)
            data = response.json()
            
            if data['success']:
                img_url = data['data']['url']
                
                # ৩. ডাটাবেসে লিংক সেভ করা
                supabase.table('submissions').insert({
                    'user_id': session['user_id'],
                    'task_id': task_id,
                    'proof_link': img_url,
                    'status': 'pending'
                }).execute()
                
                flash("✅ স্ক্রিনশট জমা হয়েছে! এডমিন চেক করে পেমেন্ট দিবে।", "success")
                return redirect(url_for('tasks'))
            else:
                flash("❌ ছবি আপলোড ব্যর্থ হয়েছে। আবার চেষ্টা করুন।", "error")
                
        except Exception as e:
            flash(f"Error: {str(e)}", "error")

    return render_template('submit_task.html', task=task, user=g.user)


# --- ACCOUNT / MENU PAGE ---
@app.route('/account')
@login_required
def account():
    # রেফারেল লিংক তৈরির জন্য ডোমেইন নেম দরকার, কিন্তু আমরা ফ্রন্টএন্ড JS দিয়ে হ্যান্ডেল করব
    return render_template('account.html', user=g.user, settings=g.settings)
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            session['user_id'] = res.user.id
            session['access_token'] = res.session.access_token
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash("❌ ইমেইল বা পাসওয়ার্ড ভুল হয়েছে।", "error")
    return render_template('login.html')

# --- REGISTER ROUTE (UNIQUE REFERRAL SYSTEM) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    # GET: রেফারেল লিংক থেকে আসলে কোড ধরা
    if request.method == 'GET':
        ref_code = request.args.get('ref')
        return render_template('register.html', ref_code=ref_code)

    # POST: ফরম সাবমিট
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        used_ref_code = request.form.get('ref_code') # যে রেফার করেছে তার কোড
        
        try:
            # ১. সাইন আপ (Supabase Auth)
            res = supabase.auth.sign_up({"email": email, "password": password})
            new_user_id = res.user.id
            
            # ২. নিজের জন্য ইউনিক কোড তৈরি করা (যেমন: TK4092)
            my_unique_code = generate_ref_code()
            
            # ৩. ডাটাবেসে নিজের কোড আপডেট করা
            supabase.table('profiles').update({
                'referral_code': my_unique_code
            }).eq('id', new_user_id).execute()

            # ৪. যদি কারো রেফারে এসে থাকে (Bonus System)
            if used_ref_code:
                try:
                    # রেফারার খুঁজে বের করা
                    referrer_res = supabase.table('profiles').select('*').eq('referral_code', used_ref_code).single().execute()
                    referrer = referrer_res.data
                    
                    if referrer:
                        # বোনাস দেওয়া (৫ টাকা)
                        new_balance = float(referrer['balance']) + 5.00
                        
                        supabase.table('profiles').update({
                            'balance': new_balance
                        }).eq('id', referrer['id']).execute()
                        
                        # নতুন ইউজারের 'referred_by' সেট করা
                        supabase.table('profiles').update({
                            'referred_by': referrer['id']
                        }).eq('id', new_user_id).execute()
                        
                except Exception as e:
                    print(f"Referral Error: {e}")

            flash("✅ একাউন্ট তৈরি হয়েছে! লগিন করুন।", "success")
            return redirect(url_for('login'))
            
        except Exception as e:
            flash("❌ রেজিস্ট্রেশন ব্যর্থ হয়েছে।", "error")
            return redirect(url_for('register'))
            
    return render_template('register.html')
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html', user=g.user, settings=g.settings)

@app.route('/tasks')
@login_required
def tasks():
    response = supabase.table('tasks').select('*').eq('is_active', True).execute()
    return render_template('tasks.html', tasks=response.data, user=g.user)

@app.route('/activate')
@login_required
def activate_account():
    return render_template('activation.html', user=g.user)

@app.route('/activate/submit', methods=['POST'])
@login_required
def submit_activation():
    trx_id = request.form.get('trx_id')
    flash("✅ রিকোয়েস্ট জমা হয়েছে। এডমিন চেক করে এপ্রুভ করবেন।", "success")
    return redirect(url_for('activate_account'))

# -------------------------------------------------------------------
# 5. ADMIN PANEL
# -------------------------------------------------------------------
@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_panel():
    if request.method == 'POST':
        m_mode = True if request.form.get('maintenance') == 'on' else False
        a_req = True if request.form.get('activation') == 'on' else False
        notice = request.form.get('notice')

        try:
            supabase.table('site_settings').update({
                'maintenance_mode': m_mode,
                'activation_required': a_req,
                'notice_text': notice
            }).eq('id', 1).execute()

            flash("✅ সেটিংস সফলভাবে সেভ হয়েছে!", "success")
            return redirect(url_for('admin_panel'))
        except Exception as e:
            flash(f"Error: {str(e)}", "error")

    try:
        user_count = supabase.table('profiles').select('*', count='exact').execute().count
    except:
        user_count = 0

    return render_template('admin.html', user=g.user, settings=g.settings, user_count=user_count)

if __name__ == '__main__':
    app.run(debug=True)
