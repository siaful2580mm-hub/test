import os
import random
import string
import requests
import base64
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import timedelta
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "TypeYourRandomSecretKeyHere123")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7) # ৭ দিন লগিন থাকবে
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
    এই ফাংশনটি প্রতিবার পেজ লোড হওয়ার আগে রান হয়।
    এটি চেক করে: ১. মেইনটেনেন্স মোড ২. ইউজার লগিন আছে কিনা ৩. এক্টিভেশন স্ট্যাটাস
    """
    
    # ১. সাইট সেটিংস লোড করা (Global Settings)
    try:
        # ডাটাবেস থেকে সেটিংস আনার চেষ্টা
        response = supabase.table('site_settings').select('*').eq('id', 1).single().execute()
        g.settings = response.data
    except:
        # ডাটাবেস ফেইল করলে ডিফল্ট সেটিংস (যাতে সাইট ক্র্যাশ না করে)
        g.settings = {'maintenance_mode': False, 'activation_required': False, 'notice_text': ''}

    # ২. ইউজার লোড করা (User Session Check) - [FIXED LOGOUT ISSUE]
    g.user = None
    if 'user_id' in session:
        try:
            user_resp = supabase.table('profiles').select('*').eq('id', session['user_id']).single().execute()
            g.user = user_resp.data
        except Exception as e:
            # ⚠️ আগে এখানে session.clear() ছিল, তাই নেট স্লো হলে লগআউট হয়ে যেত।
            # এখন আমরা লগআউট করছি না, শুধু g.user ফাঁকা রাখছি।
            # যদি সত্যি ইউজার না থাকে, তবে login_required ডেকোরেটর তাকে পরে লগইন পেজে পাঠাবে।
            print(f"Database/User Fetch Error: {e}") 
            # session.clear() <--- এই লাইনটি ডিলিট করা হয়েছে

    # ৩. মেইনটেনেন্স মোড চেক (Maintenance Mode)
    if g.settings.get('maintenance_mode'):
        # এই পেজগুলো মেইনটেনেন্স মোডেও দেখা যাবে
        allowed_public = ['static', 'login', 'logout', 'admin_login']
        
        if request.endpoint in allowed_public:
            return
        
        # এডমিন হলে সব পেজ দেখতে পারবে
        if g.user and g.user.get('role') == 'admin':
            return
            
        # বাকিদের মেইনটেনেন্স পেজ দেখাবে
        return render_template('maintenance.html')

    # ৪. এক্টিভেশন চেক (Pay to Earn Logic)
    # লজিক: আনভেরিফাইড ইউজার ড্যাশবোর্ড দেখবে, কিন্তু কাজ (Tasks) করতে পারবে না।
    if g.settings.get('activation_required'):
        # যদি ইউজার লগিন থাকে + আনভেরিফাইড হয় + এডমিন না হয়
        if g.user and not g.user.get('is_active') and g.user.get('role') != 'admin':
            
            # ক. যদি টাস্ক পেজে বা টাস্ক সাবমিট করতে যায় -> আটকাও
            restricted_pages = ['tasks', 'submit_task']
            
            if request.endpoint in restricted_pages:
                flash("⚠️ কাজ শুরু করার জন্য একাউন্ট ভেরিফাই করুন!", "error")
                return redirect(url_for('activate_account'))
            
            # খ. অন্য সব পেজ (Dashboard, History, Account) দেখতে পারবে।
            # তাই এখানে আর কোনো return বা redirect নেই।
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
    return render_template('home.html')
# --- NOTICE BOARD ROUTE ---
@app.route('/notice', methods=['GET', 'POST'])
@login_required
def notice():
    # ১. নতুন নোটিশ পোস্ট করা (শুধুমাত্র এডমিন)
    if request.method == 'POST':
        # সিকিউরিটি চেক: এডমিন না হলে রিজেক্ট
        if g.user.get('role') != 'admin':
            flash("⚠️ শুধুমাত্র এডমিন নোটিশ দিতে পারবে।", "error")
            return redirect(url_for('notice'))

        title = request.form.get('title')
        content = request.form.get('content')

        try:
            supabase.table('notices').insert({
                'title': title,
                'content': content
            }).execute()
            flash("✅ নোটিশ পাবলিশ করা হয়েছে!", "success")
        except Exception as e:
            flash("Error publishing notice", "error")
            
        return redirect(url_for('notice'))

    # ২. সব নোটিশ লোড করা (সবার জন্য)
    try:
        res = supabase.table('notices').select('*').order('created_at', desc=True).execute()
        notices = res.data
    except:
        notices = []

    return render_template('notice.html', notices=notices, user=g.user)

# --- ADMIN: VIEW WITHDRAWAL REQUESTS ---
@app.route('/admin/withdrawals')
@login_required
@admin_required
def admin_withdrawals():
    # ১. পেন্ডিং রিকোয়েস্ট আনা
    res = supabase.table('withdrawals').select('*').eq('status', 'pending').order('created_at', desc=True).execute()
    withdrawals = res.data
    
    # ২. ইউজার ইমেইল যুক্ত করা
    final_data = []
    for item in withdrawals:
        try:
            user = supabase.table('profiles').select('email').eq('id', item['user_id']).single().execute().data
            item['user_email'] = user['email']
            final_data.append(item)
        except:
            continue # ইউজার না পাওয়া গেলে স্কিপ

    return render_template('admin_withdrawals.html', requests=final_data)

# --- PUBLIC TUTORIAL PAGE ---
@app.route('/tutorial')
def tutorial():
    # g.user পাস করছি যাতে লগিন থাকলে নেভিগেশন বার ঠিক থাকে
    # লগিন না থাকলে g.user None থাকবে (before_request হ্যান্ডেল করবে)
    return render_template('tutorial.html', user=g.user if 'user' in g else None)
    
# --- ADMIN: APPROVE / REJECT WITHDRAWAL ---
@app.route('/admin/withdraw/<action>/<int:id>')
@login_required
@admin_required
def withdraw_action(action, id):
    try:
        # ১. রিকোয়েস্ট ডিটেইলস আনা
        res = supabase.table('withdrawals').select('*').eq('id', id).single().execute()
        request_data = res.data
        
        if not request_data:
            flash("রিকোয়েস্ট পাওয়া যায়নি!", "error")
            return redirect(url_for('admin_withdrawals'))

        # ২. যদি APPROVE করা হয়
        if action == 'approve':
            supabase.table('withdrawals').update({
                'status': 'approved'
            }).eq('id', id).execute()
            
            flash("✅ উইথড্রয়াল অ্যাপ্রুভ করা হয়েছে!", "success")

        # ৩. যদি REJECT করা হয় (টাকা রিফান্ড হবে)
        elif action == 'reject':
            # A. ইউজারের বর্তমান ব্যালেন্স আনা
            user_res = supabase.table('profiles').select('balance').eq('id', request_data['user_id']).single().execute()
            current_balance = float(user_res.data['balance'])
            
            # B. টাকা ফেরত দেওয়া (Refund)
            refund_amount = float(request_data['amount'])
            new_balance = current_balance + refund_amount
            
            # C. ব্যালেন্স আপডেট
            supabase.table('profiles').update({
                'balance': new_balance
            }).eq('id', request_data['user_id']).execute()
            
            # D. স্ট্যাটাস রিজেক্ট করা
            supabase.table('withdrawals').update({
                'status': 'rejected'
            }).eq('id', id).execute()
            
            flash(f"❌ রিজেক্ট করা হয়েছে। ৳{refund_amount} রিফান্ড করা হয়েছে।", "warning")

    except Exception as e:
        flash(f"Error: {str(e)}", "error")

    return redirect(url_for('admin_withdrawals'))
    
# --- REFERRAL LIST ROUTE ---
@app.route('/referrals')
@login_required
def referrals():
    try:
        # ১. যারা আমার রেফারে জয়েন করেছে তাদের লিস্ট আনা
        response = supabase.table('profiles').select('*').eq('referred_by', session['user_id']).order('created_at', desc=True).execute()
        referred_users = response.data
        
        # ২. মোট সংখ্যা
        count = len(referred_users)
        
    except Exception as e:
        print(f"Ref Error: {e}")
        referred_users = []
        count = 0

    return render_template('referrals.html', referrals=referred_users, count=count, user=g.user)
    
# --- DELETE NOTICE (ADMIN ONLY) ---
@app.route('/notice/delete/<int:id>')
@login_required
@admin_required
def delete_notice(id):
    try:
        supabase.table('notices').delete().eq('id', id).execute()
        flash("🗑️ নোটিশ ডিলিট করা হয়েছে।", "success")
    except:
        flash("Error deleting notice", "error")
        
    return redirect(url_for('notice'))

# --- ADMIN: ADD TASK & VIEW LIST ---
@app.route('/adtask', methods=['GET', 'POST'])
@login_required
@admin_required
def add_task():
    # ১. নতুন টাস্ক যোগ করা (POST)
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        link = request.form.get('link')
        try:
            reward = float(request.form.get('reward'))
        except:
            reward = 0.0
        category = request.form.get('category')
        task_type = request.form.get('task_type')
        
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

    # ২. সব টাস্কের লিস্ট আনা (GET)
    try:
        # নতুন টাস্ক আগে দেখাবে
        res = supabase.table('tasks').select('*').order('id', desc=True).execute()
        all_tasks = res.data
    except:
        all_tasks = []
        
    return render_template('adtask.html', user=g.user, tasks=all_tasks)


# --- ADMIN: DELETE TASK ---
@app.route('/admin/task/delete/<int:id>')
@login_required
@admin_required
def delete_task(id):
    try:
        # A. টাস্ক ডিলিট করার আগে এর সাবমিশনগুলো ডিলিট করতে হবে (Foreign Key Error এড়াতে)
        supabase.table('submissions').delete().eq('task_id', id).execute()
        
        # B. মূল টাস্ক ডিলিট করা
        supabase.table('tasks').delete().eq('id', id).execute()
        
        flash("🗑️ টাস্ক এবং এর সাবমিশন মুছে ফেলা হয়েছে।", "success")
    except Exception as e:
        flash(f"Delete Error: {str(e)}", "error")
        
    return redirect(url_for('add_task'))
# --- ADMIN: VIEW PENDING SUBMISSIONS (LIMIT 20) ---
@app.route('/admin/submissions')
@login_required
@admin_required
def admin_submissions():
    # ১. মাত্র ২০টি পেন্ডিং ডাটা আনা (Performance এর জন্য)
    # .limit(20) যোগ করা হয়েছে
    subs_res = supabase.table('submissions').select('*').eq('status', 'pending').order('created_at', desc=True).limit(20).execute()
    submissions = subs_res.data
    
    # ২. ডাটা প্রসেসিং (User Email এবং Task Title বের করা)
    final_data = []
    for sub in submissions:
        try:
            # ইউজার ইনফো
            user = supabase.table('profiles').select('email').eq('id', sub['user_id']).single().execute().data
            # টাস্ক ইনফো
            task = supabase.table('tasks').select('title, reward').eq('id', sub['task_id']).single().execute().data
            
            sub['user_email'] = user['email']
            sub['task_title'] = task['title']
            sub['reward'] = task['reward']
            final_data.append(sub)
        except:
            continue 

    # টোটাল পেন্ডিং কাউন্ট চেক করা (বোঝার জন্য আরও কত বাকি আছে)
    try:
        count_res = supabase.table('submissions').select('id', count='exact', head=True).eq('status', 'pending').execute()
        total_pending = count_res.count
    except:
        total_pending = len(final_data)

    return render_template('submissions.html', submissions=final_data, total_pending=total_pending)

# --- ADMIN: BULK APPROVE (FIXED & STRICT) ---
@app.route('/admin/submissions/bulk-approve')
@login_required
@admin_required
def bulk_approve():
    try:
        # ১. ২০টি পেন্ডিং সাবমিশন আনা
        subs_res = supabase.table('submissions').select('*').eq('status', 'pending').limit(20).execute()
        submissions = subs_res.data
        
        if not submissions:
            flash("⚠️ কোনো পেন্ডিং টাস্ক পাওয়া যায়নি।", "warning")
            return redirect(url_for('admin_submissions'))

        success_count = 0
        
        # ২. লুপ চালিয়ে কাজ করা
        for sub in submissions:
            try:
                # A. টাস্কের টাকার পরিমাণ জানা
                task_res = supabase.table('tasks').select('reward').eq('id', sub['task_id']).single().execute()
                if not task_res.data: continue # টাস্ক না পেলে স্কিপ
                reward = float(task_res.data['reward'])
                
                # B. ইউজারের বর্তমান ব্যালেন্স জানা
                user_res = supabase.table('profiles').select('balance').eq('id', sub['user_id']).single().execute()
                if not user_res.data: continue # ইউজার না পেলে স্কিপ
                current_balance = float(user_res.data['balance'])
                
                # C. নতুন ব্যালেন্স আপডেট করা
                new_balance = current_balance + reward
                supabase.table('profiles').update({'balance': new_balance}).eq('id', sub['user_id']).execute()
                
                # D. সাবমিশন স্ট্যাটাস 'approved' করা (Critial Step)
                update_res = supabase.table('submissions').update({'status': 'approved'}).eq('id', sub['id']).execute()
                
                # চেক করা: আসলেই আপডেট হয়েছে কিনা?
                if len(update_res.data) > 0:
                    success_count += 1
                    
            except Exception as loop_e:
                print(f"Error for sub {sub['id']}: {loop_e}")
                continue

        # ৩. ফলাফল জানানো
        if success_count > 0:
            flash(f"✅ সফলভাবে {success_count}টি টাস্ক অ্যাপ্রুভ এবং টাকা যোগ করা হয়েছে!", "success")
        else:
            flash("❌ সার্ভার এরর: ডাটাবেস আপডেট হয়নি। ম্যানুয়ালি চেষ্টা করুন।", "error")

    except Exception as e:
        flash(f"System Error: {str(e)}", "error")

    return redirect(url_for('admin_submissions'))



# --- ADMIN: FILTER NEW USERS (CSV COPY) ---
@app.route('/admin/user-check')
@login_required
@admin_required
def admin_user_check():
    try:
        # ১. গত ২৪ ঘন্টার সময় বের করা (UTC Time)
        last_24_hours = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        # ২. কুয়েরি চালানো
        # শর্ত: balance 10-50, created_at >= 24h, email contains @gmail.com
        res = supabase.table('profiles').select('email') \
            .gte('balance', 10) \
            .lte('balance', 50) \
            .gte('created_at', last_24_hours) \
            .ilike('email', '%@gmail.com') \
            .limit(290) \
            .execute()
            
        users = res.data
        
        # ৩. শুধু ইমেইলগুলো কমা (,) দিয়ে আলাদা করে স্ট্রিং বানানো (CSV Format)
        email_list = [u['email'] for u in users]
        csv_data = ", ".join(email_list)
        count = len(email_list)
        
    except Exception as e:
        print(f"Filter Error: {e}")
        csv_data = ""
        count = 0

    return render_template('user_check.html', csv_data=csv_data, count=count)# --- ADMIN: APPROVE / REJECT ACTION (FIXED) ---
@app.route('/admin/submission/<action>/<int:sub_id>')
@login_required
@admin_required
def submission_action(action, sub_id):
    try:
        # ১. সাবমিশন ডিটেইলস খুঁজে বের করা
        sub_res = supabase.table('submissions').select('*').eq('id', sub_id).single().execute()
        submission = sub_res.data
        
        if not submission:
            flash("❌ সাবমিশন পাওয়া যায়নি!", "error")
            return redirect(url_for('admin_submissions'))

        # ২. ডাবল পেমেন্ট আটকানো (যদি অলরেডি অ্যাপ্রুভড থাকে)
        if submission['status'] == 'approved':
            flash("⚠️ এটি আগেই অ্যাপ্রুভ করা হয়েছে!", "warning")
            return redirect(url_for('admin_submissions'))

        # ৩. যদি একশন 'approve' হয়
        if action == 'approve':
            # A. টাস্কের টাকার পরিমাণ জানা
            task_res = supabase.table('tasks').select('reward').eq('id', submission['task_id']).single().execute()
            reward = float(task_res.data['reward'])
            
            # B. ইউজারের বর্তমান ব্যালেন্স জানা
            user_res = supabase.table('profiles').select('balance').eq('id', submission['user_id']).single().execute()
            # ব্যালেন্স যদি NULL থাকে তবে 0 ধরবে
            current_balance = float(user_res.data['balance']) if user_res.data['balance'] else 0.0
            
            # C. নতুন ব্যালেন্স হিসাব করা
            new_balance = current_balance + reward
            
            # D. প্রোফাইল টেবিলে ব্যালেন্স আপডেট করা
            supabase.table('profiles').update({
                'balance': new_balance
            }).eq('id', submission['user_id']).execute()
            
            # E. সাবমিশন স্ট্যাটাস 'approved' করা
            supabase.table('submissions').update({
                'status': 'approved'
            }).eq('id', sub_id).execute()
            
            flash(f"✅ অ্যাপ্রুভ সফল! ইউজার ৳{reward} পেয়েছে।", "success")

        # ৪. যদি একশন 'reject' হয়
        elif action == 'reject':
            supabase.table('submissions').update({
                'status': 'rejected'
            }).eq('id', sub_id).execute()
            flash("❌ রিজেক্ট করা হয়েছে।", "error")

    except Exception as e:
        print(f"Error: {e}") # Vercel Logs এ এরর দেখার জন্য
        flash(f"ত্রুটি হয়েছে: {str(e)}", "error")

    return redirect(url_for('admin_submissions'))


# --- WITHDRAW ROUTE (FIXED & RELIABLE COUNT) ---
@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    # ১. রেফারেল সংখ্যা গণনা (সবচেয়ে নির্ভরযোগ্য পদ্ধতি)
    try:
        # সরাসরি আইডিগুলো নিয়ে এসে Python দিয়ে গুনব (এটি ভুল হওয়ার সুযোগ নেই)
        response = supabase.table('profiles').select('id').eq('referred_by', session['user_id']).execute()
        ref_count = len(response.data) # ডাটাবেস থেকে আসা লিস্টের দৈর্ঘ্য
        
        # ডিবাগিং (Vercel Logs এ দেখার জন্য)
        print(f"User: {session['user_id']} | Real Count: {ref_count}")
        
    except Exception as e:
        print(f"Counting Error: {e}")
        ref_count = 0

    # ২. ব্যালেন্স লোড
    current_balance = float(g.user.get('balance', 0.0))

    # ৩. ফর্ম সাবমিট হলে (POST Request)
    if request.method == 'POST':
        method = request.form.get('method')
        number = request.form.get('number')
        try:
            amount = float(request.form.get('amount'))
        except:
            amount = 0

        # --- শর্ত চেক ---
        
        # শর্ত ১: ৩টি রেফারেল
        if ref_count < 3:
            flash(f"❌ উইথড্র করতে ৩টি রেফার প্রয়োজন। আপনার আছে: {ref_count}টি।", "error")
            return redirect(url_for('withdraw'))

        # শর্ত ২: মিনিমাম ২৫০ টাকা
        if amount < 250:
            flash("❌ সর্বনিম্ন উইথড্রয়াল ২৫০ টাকা।", "error")
            return redirect(url_for('withdraw'))

        # শর্ত ৩: পর্যাপ্ত ব্যালেন্স
        if amount > current_balance:
            flash("❌ আপনার একাউন্টে পর্যাপ্ত টাকা নেই।", "error")
            return redirect(url_for('withdraw'))

        # --- সব ঠিক থাকলে রিকোয়েস্ট জমা ---
        try:
            # A. রিকোয়েস্ট সেভ
            supabase.table('withdrawals').insert({
                'user_id': session['user_id'],
                'method': method,
                'number': number,
                'amount': amount,
                'status': 'pending'
            }).execute()

            # B. ব্যালেন্স থেকে টাকা কাটা
            new_balance = current_balance - amount
            supabase.table('profiles').update({
                'balance': new_balance
            }).eq('id', session['user_id']).execute()

            flash("✅ সফল! আপনার উইথড্র রিকোয়েস্ট জমা হয়েছে।", "success")
            return redirect(url_for('history'))

        except Exception as e:
            flash(f"Error: {str(e)}", "error")

    # ৪. পেজ দেখানো (GET Request)
    return render_template('withdraw.html', user=g.user, ref_count=ref_count)
    # --- USER: SUBMIT TASK (ImgBB Upload) ---
# --- USER: SUBMIT TASK (WITH DUPLICATE CHECK) ---
@app.route('/task/submit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def submit_task(task_id):
    # টাস্ক ডিটেইলস আনা
    try:
        task_res = supabase.table('tasks').select('*').eq('id', task_id).single().execute()
        task = task_res.data
    except:
        flash("টাস্ক পাওয়া যায়নি।", "error")
        return redirect(url_for('tasks'))

    # ১. [NEW] চেক করা: ইউজার কি আগেই এই টাস্ক সাবমিট করেছে?
    existing_sub = supabase.table('submissions').select('id').eq('user_id', session['user_id']).eq('task_id', task_id).execute()
    
    if len(existing_sub.data) > 0:
        flash("⚠️ আপনি ইতিমধ্যে এই কাজটি জমা দিয়েছেন!", "warning")
        return redirect(url_for('tasks'))

    if request.method == 'POST':
        if 'screenshot' not in request.files:
            flash("ছবি আপলোড করুন!", "error")
            return redirect(request.url)
            
        file = request.files['screenshot']
        if file.filename == '':
            flash("কোনো ছবি সিলেক্ট করা হয়নি", "error")
            return redirect(request.url)

        try:
            # ২. ImgBB তে আপলোড করা
            api_key = "f5789c14135a479b4e3893c6b9ccf074" 
            image_string = base64.b64encode(file.read())
            
            payload = {
                "key": api_key,
                "image": image_string,
            }
            
            response = requests.post("https://api.imgbb.com/1/upload", data=payload)
            data = response.json()
            
            if data['success']:
                img_url = data['data']['url']
                
                # ৩. ডাটাবেসে সেভ করা
                supabase.table('submissions').insert({
                    'user_id': session['user_id'],
                    'task_id': task_id,
                    'proof_link': img_url,
                    'status': 'pending'
                }).execute()
                
                flash("✅ সফলভাবে জমা হয়েছে! এডমিন চেক করে পেমেন্ট দিবে।", "success")
                return redirect(url_for('tasks'))
            else:
                flash("❌ ছবি আপলোড ব্যর্থ হয়েছে।", "error")
                
        except Exception as e:
            flash(f"Error: {str(e)}", "error")

    return render_template('submit_task.html', task=task, user=g.user)# --- ACCOUNT PAGE ROUTE (WITH REFERRAL COUNT) ---
@app.route('/account')
@login_required
def account():
    # ১. রেফারেল সংখ্যা গণনা (Fix)
    try:
        # ডাটাবেস থেকে চেক করছি কতজন ইউজারের 'referred_by' আমার ID
        response = supabase.table('profiles').select('id').eq('referred_by', session['user_id']).execute()
        
        # লিস্টের দৈর্ঘ্যই হলো মোট রেফারেল সংখ্যা
        ref_count = len(response.data)
        
    except Exception as e:
        # কোনো এরর হলে ০ দেখাবে
        print(f"Account Page Error: {e}")
        ref_count = 0

    # ২. টেমপ্লেট রেন্ডার করা (ref_count পাস করা হলো)
    return render_template('account.html', user=g.user, settings=g.settings, ref_count=ref_count)
# --- LOGIN ROUTE (FIXED SESSION) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    # যদি ইউজার ইতিমধ্যে লগিন থাকে, তবে ড্যাশবোর্ডে পাঠাও
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # ১. Supabase দিয়ে লগিন চেক করা
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            
            # ২. সেশন স্থায়ী করা (যাতে লগআউট না হয়)
            session.permanent = True  # <--- এই লাইনটি খুবই গুরুত্বপূর্ণ
            
            # ৩. সেশনে ডাটা রাখা
            session['user_id'] = res.user.id
            session['access_token'] = res.session.access_token
            
            flash("✅ স্বাগতম! আপনি সফলভাবে লগিন করেছেন।", "success")
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            # পাসওয়ার্ড ভুল হলে
            flash("❌ ইমেইল বা পাসওয়ার্ড ভুল হয়েছে। আবার চেষ্টা করুন।", "error")
            print(f"Login Error: {e}") # ডিবাগিং এর জন্য
            
    return render_template('login.html')
# --- REGISTER ROUTE (UNIQUE REFERRAL SYSTEM) ---
# --- REGISTER ROUTE (BOTH GET BONUS 10 TAKA) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    # GET: লিংক থেকে আসলে কোড ধরা
    if request.method == 'GET':
        ref_code = request.args.get('ref')
        return render_template('register.html', ref_code=ref_code)

    # POST: ফরম সাবমিট
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        used_ref_code = request.form.get('ref_code') # হিডেন ইনপুট থেকে কোড
        
        try:
            # ১. সাইন আপ (Supabase Auth)
            res = supabase.auth.sign_up({"email": email, "password": password})
            new_user_id = res.user.id
            
            # ২. নিজের জন্য ইউনিক কোড তৈরি (TK + Random)
            chars = string.ascii_uppercase + string.digits
            my_unique_code = 'TK' + ''.join(random.choices(chars, k=4))
            
            # ৩. নিজের প্রোফাইল আপডেট (Referral Code সেট করা)
            # ডিফল্ট ব্যালেন্স ০ থাকে
            supabase.table('profiles').update({
                'referral_code': my_unique_code
            }).eq('id', new_user_id).execute()

            # ৪. রেফারেল বোনাস লজিক (উভয়ের জন্য ১০ টাকা)
            if used_ref_code and used_ref_code != '':
                try:
                    # যার কোড ব্যবহার হয়েছে তাকে খোঁজা
                    referrer_res = supabase.table('profiles').select('*').eq('referral_code', used_ref_code).single().execute()
                    referrer = referrer_res.data
                    
                    if referrer:
                        referrer_id = referrer['id']
                        
                        # A. লিংক করা (Referred By সেট করা)
                        supabase.table('profiles').update({
                            'referred_by': referrer_id
                        }).eq('id', new_user_id).execute()
                        
                        # B. রেফারারকে ১০ টাকা বোনাস দেওয়া
                        ref_balance = float(referrer['balance']) + 10.00
                        supabase.table('profiles').update({
                            'balance': ref_balance
                        }).eq('id', referrer_id).execute()

                        # C. নতুন ইউজারকে ১০ টাকা বোনাস দেওয়া
                        # যেহেতু নতুন, তাই সরাসরি ১০ সেট করে দিলেই হবে
                        supabase.table('profiles').update({
                            'balance': 10.00
                        }).eq('id', new_user_id).execute()
                        
                except Exception as e:
                    print(f"Referral Error: {e}") 
                    # রেফারেল ফেইল করলেও রেজিস্ট্রেশন আটকাবে না

            flash("✅ একাউন্ট তৈরি হয়েছে! লগিন করুন।", "success")
            return redirect(url_for('login'))
            
        except Exception as e:
            flash("❌ রেজিস্ট্রেশন ব্যর্থ হয়েছে। ইমেইলটি হয়তো আগেই ব্যবহৃত।", "error")
            print(f"Reg Error: {e}")
            return redirect(url_for('register'))
            
    return render_template('register.html')
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- ADMIN: USER MANAGEMENT ---

# 1. User List & Search
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    search_query = request.args.get('q')
    
    # বেসিক কুয়েরি
    query = supabase.table('profiles').select('*').order('created_at', desc=True)
    
    # যদি সার্চ করা হয়
    if search_query:
        query = query.ilike('email', f'%{search_query}%')
        
    try:
        users = query.execute().data
    except Exception as e:
        users = []
        flash(f"Error fetching users: {str(e)}", "error")

    return render_template('users.html', users=users)

# 2. Ban / Unban User
@app.route('/admin/user/ban/<uuid:user_id>')
@login_required
@admin_required
def ban_user(user_id):
    try:
        # বর্তমান স্ট্যাটাস জানা
        user_res = supabase.table('profiles').select('is_banned').eq('id', str(user_id)).single().execute()
        current_status = user_res.data['is_banned']
        
        # স্ট্যাটাস উল্টে দেওয়া (Toggle)
        new_status = not current_status
        supabase.table('profiles').update({'is_banned': new_status}).eq('id', str(user_id)).execute()
        
        msg = "🔴 ইউজারকে ব্যান করা হয়েছে!" if new_status else "🟢 ইউজার আনব্যান হয়েছে!"
        flash(msg, "success")
        
    except Exception as e:
        flash("Action Failed", "error")
        
    return redirect(url_for('admin_users'))

# 3. Delete User Profile
@app.route('/admin/user/delete/<uuid:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    try:
        # প্রোফাইল ডিলিট (Auth User থেকে যাবে, কিন্তু ডাটা মুছে যাবে)
        supabase.table('profiles').delete().eq('id', str(user_id)).execute()
        flash("🗑️ ইউজার প্রোফাইল ডিলিট করা হয়েছে।", "success")
    except Exception as e:
        flash(f"Delete Failed: {str(e)}", "error")
        
    return redirect(url_for('admin_users'))

# 4. Update Balance
@app.route('/admin/user/balance', methods=['POST'])
@login_required
@admin_required
def update_user_balance():
    user_id = request.form.get('user_id')
    new_balance = request.form.get('amount')
    
    try:
        supabase.table('profiles').update({
            'balance': float(new_balance)
        }).eq('id', user_id).execute()
        
        flash("💰 ব্যালেন্স আপডেট করা হয়েছে!", "success")
    except Exception as e:
        flash("Update Failed", "error")
        
    return redirect(url_for('admin_users'))
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html', user=g.user, settings=g.settings)
# --- 1. UPDATED TASKS ROUTE (Hide Completed Tasks) ---
@app.route('/tasks')
@login_required
def tasks():
    try:
        # A. সব অ্যাক্টিভ টাস্ক আনা (নতুন টাস্ক আগে থাকবে)
        # .order('id', desc=True) যোগ করা হয়েছে
        all_tasks = supabase.table('tasks').select('*').eq('is_active', True).order('id', desc=True).execute().data
        
        # B. ইউজার ইতিমধ্যে যেসব টাস্ক সাবমিট করেছে তাদের ID আনা
        submitted_res = supabase.table('submissions').select('task_id').eq('user_id', session['user_id']).execute()
        
        # লিস্ট কম্প্রিহেনশন দিয়ে ID গুলো আলাদা করা
        completed_task_ids = [item['task_id'] for item in submitted_res.data]
        
        # C. ফিল্টারিং: যেসব টাস্ক completed লিস্টে নেই, শুধু সেগুলোই দেখাবে
        available_tasks = [task for task in all_tasks if task['id'] not in completed_task_ids]
        
    except Exception as e:
        available_tasks = []
        print(f"Error: {e}")

    return render_template('tasks.html', tasks=available_tasks, user=g.user)
# --- 2. NEW HISTORY ROUTE (Task & Withdraw) ---
@app.route('/history')
@login_required
def history():
    # A. কাজের হিস্টোরি (Task Submissions)
    try:
        subs_res = supabase.table('submissions').select('*').eq('user_id', session['user_id']).order('created_at', desc=True).execute()
        my_tasks = subs_res.data
        
        # টাস্কের নাম (Title) যুক্ত করা (যেহেতু submissions টেবিলে শুধু ID আছে)
        for item in my_tasks:
            try:
                task_info = supabase.table('tasks').select('title, reward').eq('id', item['task_id']).single().execute()
                item['title'] = task_info.data['title']
                item['reward'] = task_info.data['reward']
            except:
                item['title'] = "Unknown Task" # যদি টাস্ক ডিলিট হয়ে যায়
                item['reward'] = 0
    except:
        my_tasks = []

    # B. উইথড্রয়াল হিস্টোরি (Withdrawals)
    try:
        with_res = supabase.table('withdrawals').select('*').eq('user_id', session['user_id']).order('created_at', desc=True).execute()
        my_withdrawals = with_res.data
    except:
        my_withdrawals = []

    return render_template('history.html', tasks=my_tasks, withdrawals=my_withdrawals, user=g.user)
# --- USER: ACTIVATION PAGE & STATUS CHECK ---
@app.route('/activate')
@login_required
def activate_account():
    # ১. যদি ইউজার ইতিমধ্যে এক্টিভ থাকে, ড্যাশবোর্ডে পাঠাও
    if g.user.get('is_active'):
        flash("✅ আপনার একাউন্ট ইতিমধ্যে ভেরিফাইড!", "success")
        return redirect(url_for('dashboard'))

    # ২. চেক করা ইউজার আগে কোনো রিকোয়েস্ট পাঠিয়েছে কিনা
    try:
        req_res = supabase.table('activation_requests').select('*').eq('user_id', session['user_id']).order('created_at', desc=True).limit(1).execute()
        existing_request = req_res.data[0] if req_res.data else None
    except:
        existing_request = None

    return render_template('activation.html', user=g.user, request_data=existing_request)


# --- USER: SUBMIT REQUEST (ONLY ONCE) ---
@app.route('/activate/submit', methods=['POST'])
@login_required
def submit_activation():
    # ১. আবার চেক করা ইউজার অলরেডি সাবমিট করেছে কিনা (ডাবল সাবমিশন রোধ)
    try:
        check_res = supabase.table('activation_requests').select('*').eq('user_id', session['user_id']).eq('status', 'pending').execute()
        if check_res.data:
            flash("⚠️ আপনার একটি রিকোয়েস্ট ইতিমধ্যে পেন্ডিং আছে। অপেক্ষা করুন।", "warning")
            return redirect(url_for('activate_account'))
    except:
        pass

    # ২. ফর্ম ডাটা নেওয়া
    method = request.form.get('method')
    sender_number = request.form.get('sender_number')
    trx_id = request.form.get('trx_id')
    
    try:
        # ৩. ডাটাবেসে সেভ করা
        supabase.table('activation_requests').insert({
            'user_id': session['user_id'],
            'method': method,
            'sender_number': sender_number,
            'trx_id': trx_id,
            'status': 'pending'
        }).execute()
        
        flash("✅ তথ্য জমা হয়েছে! এডমিন শীঘ্রই যাচাই করবেন।", "success")
        
    except Exception as e:
        print(f"Activation Error: {e}")
        flash("❌ ডাটা সেভ হয়নি। আবার চেষ্টা করুন।", "error")
        
    return redirect(url_for('activate_account'))
    
# --- ADMIN: APPROVE / REJECT ACTIVATION ---
@app.route('/admin/activation/<action>/<int:req_id>')
@login_required
@admin_required
def activation_action(action, req_id):
    try:
        # ১. রিকোয়েস্ট ডিটেইলস আনা
        req_res = supabase.table('activation_requests').select('*').eq('id', req_id).single().execute()
        req_data = req_res.data
        
        if not req_data:
            flash("রিকোয়েস্ট পাওয়া যায়নি!", "error")
            return redirect(url_for('admin_activations'))

        # ২. যদি APPROVE করা হয়
        if action == 'approve':
            # A. ইউজারকে Active করা (Main Job)
            supabase.table('profiles').update({
                'is_active': True
            }).eq('id', req_data['user_id']).execute()
            
            # B. রিকোয়েস্ট স্ট্যাটাস আপডেট
            supabase.table('activation_requests').update({
                'status': 'approved'
            }).eq('id', req_id).execute()
            
            flash(f"✅ ইউজার সফলভাবে অ্যাক্টিভ হয়েছে!", "success")

        # ৩. যদি REJECT করা হয়
        elif action == 'reject':
            supabase.table('activation_requests').update({
                'status': 'rejected'
            }).eq('id', req_id).execute()
            flash("❌ রিকোয়েস্ট বাতিল করা হয়েছে।", "error")

    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        
    return redirect(url_for('admin_activations'))


# --- ADMIN: VIEW ACTIVATION REQUESTS ---
@app.route('/admin/activations')
@login_required
@admin_required
def admin_activations():
    # ১. পেন্ডিং রিকোয়েস্ট আনা
    req_res = supabase.table('activation_requests').select('*').eq('status', 'pending').order('created_at', desc=True).execute()
    requests_data = req_res.data
    
    # ২. ইউজার ইমেইল যুক্ত করা
    final_data = []
    for req in requests_data:
        try:
            user = supabase.table('profiles').select('email').eq('id', req['user_id']).single().execute().data
            req['user_email'] = user['email']
            final_data.append(req)
        except:
            continue

    return render_template('activations.html', requests=final_data)


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
