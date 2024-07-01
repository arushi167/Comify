from flask import Flask, request, redirect, render_template, url_for, session
from flask_oauthlib.client import OAuth
from flask_restful import Resource, Api
import os
from EasyFlaskRecaptcha import ReCaptcha
from urllib.parse import urlparse
from functools import wraps
from flask_pymongo import PyMongo
import razorpay
from dotenv import load_dotenv
load_dotenv()

MONGODB_URI                 = os.environ.get('MONGODB_URI') 
GOOGLE_CLIENT_ID            = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET        = os.environ.get('GOOGLE_CLIENT_SECRET') 
RAZORPAY_ID                 = os.environ.get('RAZORPAY_ID') 
RAZORPAY_SECRET             = os.environ.get('RAZORPAY_SECRET') 
GOOGLE_RECAPTCHA_SITE_KEY   = os.environ.get('GOOGLE_RECAPTCHA_SITE_KEY') 
GOOGLE_RECAPTCHA_SECRET_KEY = os.environ.get('GOOGLE_RECAPTCHA_SECRET_KEY') 

# Initialize Razorpay client
client = razorpay.Client(auth=(RAZORPAY_ID, RAZORPAY_SECRET))

app = Flask(__name__)
app.secret_key = 'VeryVeryComify#@666' 
app.config['SESSION_COOKIE_DOMAIN'] = '.witeso.com'  # So that Login works for all the subdomain

# Configure MongoDB
app.config['MONGO_URI'] = MONGODB_URI
mongo = PyMongo(app)
db = mongo.db 

oauth = OAuth(app)
google = oauth.remote_app(
    'google',
    consumer_key=os.environ.get('GOOGLE_CLIENT_ID', GOOGLE_CLIENT_ID),
    consumer_secret=os.environ.get('GOOGLE_CLIENT_SECRET', GOOGLE_CLIENT_SECRET),
    request_token_params={
        'scope': 'email profile',
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

# Google Captcha
recaptcha = ReCaptcha(app)

app.config.update(dict(
GOOGLE_RECAPTCHA_ENABLED=True,
GOOGLE_RECAPTCHA_SITE_KEY=GOOGLE_RECAPTCHA_SITE_KEY,
GOOGLE_RECAPTCHA_SECRET_KEY=GOOGLE_RECAPTCHA_SECRET_KEY
))
recaptcha.init_app(app)

whitelisted_domains = {'witeso.com'}

# Razarpay Routes
@app.route('/pricing', methods=["GET", "POST"])
def pricing():
    if request.method == "POST" and request.form.get("amount") != "":
        if 'google_token' not in session:
            return redirect('login?redirect=https://www.witeso.com/pricing')
        amount = int(request.form.get("amt"))
        amount = amount * 100 # Paise
        print("amt: ", amount)
        data = { "amount": amount, "currency": "INR", "receipt": "order_rcptid_11" }
        payment = client.order.create(data=data)
        pdata   = [amount, payment["id"]]
        return render_template("pricing.html", pdata=pdata, RAZORPAY_ID=RAZORPAY_ID)
    return render_template("pricing.html")

@app.route('/success', methods=["POST"])
def success():
    pid=request.form.get("razorpay_payment_id")
    ordid=request.form.get("razorpay_order_id")
    sign=request.form.get("razorpay_signature")
    params={
    'razorpay_order_id': ordid,
    'razorpay_payment_id': pid,
    'razorpay_signature': sign
    }
    final=client.utility.verify_payment_signature(params)
    if final == True:
        order = client.order.fetch(ordid)
        amount = order['amount'] / 100  # Convert amount from paise to rupees
        if amount == 10:
            credit_count = 200
        elif amount == 50:
            credit_count = 1500
        else:
            credit_count = amount * 20 

        if session["credit"] != "Unlimited":
            users_collection = db.users
            users_collection.update_one(
                {"user_id": session["id"]},
                {"$inc": {"credit": credit_count}, "$set": {"plan_type": "Premium"}}
            )
        existing_user = users_collection.find_one({"user_id": session["id"]})
        session["credit"]    = existing_user["credit"]
        session["plan_type"] = existing_user["plan_type"]
        return render_template("payment_success.html", credit_count=credit_count)
    return render_template("payment_failed.html")

# API Code
api = Api(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'google_token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def show_live_credit(f):
    @wraps(f)
    def fetch_credit(*args, **kwargs):
        if 'google_token' in session:
            users_collection = db.users
            existing_user = users_collection.find_one({"user_id": session["id"]})
            session["credit"] = existing_user["credit"]
        return f(*args, **kwargs)
    return fetch_credit

@app.route('/')
@show_live_credit
def home():
    return render_template("index.html")

@app.route('/about_us')
@show_live_credit
def about():
    users_count = db.users.count_documents({})
    return render_template("about_us.html", users_count=users_count)

@show_live_credit
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    message = None 
    if request.method == 'POST':
        if recaptcha.verify():
            # Captcha verified, proceed to save form data to MongoDB
            name    = request.form['name']
            email   = request.form['email']
            number  = request.form['number']
            subject  = request.form['subject']
            message = request.form['message']

            # Save form data to MongoDB
            data = {'name': name, 'email': email, 'number': number, 'subject': subject, 'message': message}
            db.contacts.insert_one(data)

            message = {"heading": "Contact Form Submitted!", "text": "Message Sent Successfully", "type": "success"}
        else:
            # Captcha verification failed
            message = {"heading": "Contact Form Submission Failed!", "text": "Captcha verification failed.", "type": "fail"}

    subject = request.args.get("subject")
    if subject in {'web_development', 'android_development', 'software_development', 'machine_learning', 'blockchain', 'cybersecurity'}:
        return render_template("contact.html", subject=subject, GOOGLE_RECAPTCHA_SITE_KEY=GOOGLE_RECAPTCHA_SITE_KEY, message=message)
    
    return render_template("contact.html", GOOGLE_RECAPTCHA_SITE_KEY=GOOGLE_RECAPTCHA_SITE_KEY, message=message)

@app.route('/privacy')
@show_live_credit
def privacy():
    return render_template("privacy.html")

@app.route('/cancellation_and_refund')
@show_live_credit
def cancellation_and_refund():
    return render_template("cancellation_and_refund.html")

@app.route('/shipping_and_delivery')
@show_live_credit
def shipping_and_delivery():
    return render_template("shipping_and_delivery.html")

@app.route('/terms_of_service')
@show_live_credit
def terms_of_service():
    return render_template("terms_of_service.html")

@app.route('/cloner')
def site_cloner():
    url = request.args.get('url')
    if url:
        return ""
    else:
        return "Provide Valid URL"

## Single Sign-On (SSO)
@app.route('/login')
def login():
    redirect_url = request.args.get('redirect', '/')
    if 'google_token' in session:
        return redirect(redirect_url)

    parsed_url = urlparse(redirect_url)
    callback_url = "https://www.witeso.com" + url_for('authorized') 
    if '/' == redirect_url:
        return google.authorize(callback=callback_url)
    elif parsed_url.hostname.endswith('.witeso.com') or parsed_url.hostname in whitelisted_domains:
        return google.authorize(callback=callback_url+"?next="+redirect_url)
    else:
        return 'Invalid redirect URL'

@app.route('/logout')
def logout():
    redirect_url = request.args.get('redirect', '/')
    session.clear()
    return redirect(redirect_url)

@app.route('/login/authorized')
def authorized():
    response = google.authorized_response()

    if response is None or response.get('access_token') is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )

    session['google_token'] = (response['access_token'], '')
    user_info = google.get('userinfo')
    user_id = user_info.data["id"]
    email   = user_info.data["email"]
    picture = user_info.data["picture"]
    # print("user_info: ", user_info.data)
    session["email"] = email
    session['user_full_name'] = user_info.data.get('name')
    session['picture'] = picture
    session['id'] = user_id

    # Check if the user already exists in the database
    users_collection = db.users
    existing_user = users_collection.find_one({"user_id": user_id})

    if existing_user is None:
        # Determine plan_type and credit based on email domain
        if email.endswith('@ipu.ac.in'):
            plan_type = "Premium"
            credit = "Unlimited"
        else:
            plan_type = "Freemium"
            credit = 500

        # Insert new user information into MongoDB
        user_data = {
            "user_id": user_id,
            "name": user_info.data.get('name'),
            "email": email,
            "picture": picture,
            "plan_type": plan_type,
            "credit": credit
        }
        users_collection.insert_one(user_data)
    else:
        session["credit"] = existing_user["credit"]
        session["plan_type"] = existing_user["plan_type"]

    redirect_url = request.args.get('next') or '/'
    return redirect(redirect_url)

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

if __name__ == '__main__':
    app.run(debug=True)
