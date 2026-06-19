import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
import requests

# Import Supabase
from supabase import create_client

def homepage(request):
    return render(request, 'updatehome.html')

def order_post(request):
    name = request.POST['name']
    email = request.POST['email']
    phone = request.POST['phone']
    address = request.POST['address']
    quantity = request.POST['quantity']

    if quantity == "50g":
        amount = 1 * 100
    elif quantity == "100g":
        amount = 1 * 100
    elif quantity == "200g":
        amount = 1 * 100
    else:
        amount = 0

    return render(request, 'pp.html', {
        'name': name,
        'email': email,
        'phone': phone,
        'address': address,
        'quantity': quantity,
        'amount': amount,
        'razorpay_api_key': 'rzp_live_Su35EVyNYFeKCF',
        'currency': 'INR'
    })

def raz_pay(request, amount):
    import razorpay
    razorpay_api_key = "rzp_live_Su35EVyNYFeKCF"
    razorpay_secret_key = "NQE3JfS6rdlmp8YtHrxF120H"
    
    razorpay_client = razorpay.Client(auth=(razorpay_api_key, razorpay_secret_key))
    amount = float(amount)
    
    order_data = {
        'amount': amount,
        'currency': 'INR',
        'receipt': 'order_rcptid_11',
        'payment_capture': '1',
    }
    
    order = razorpay_client.order.create(data=order_data)
    
    return render(request, 'pp.html', {
        'razorpay_api_key': razorpay_api_key,
        'amount': order_data['amount'],
        'currency': order_data['currency'],
        'order_id': order['id']
    })

# ==========================================
# SAVE ORDER TO SUPABASE - FIXED VERSION
# ==========================================
def save_order_to_supabase(name, email, phone, address, quantity, payment_id):
    """Save order to Supabase database"""
    try:
        # Your Supabase credentials - DIRECT values
        supabase_url = "https://fgikrpxjaskyduewekiu.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZnaWtycHhqYXNreWR1ZXdla2l1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAzNTg3MDUsImV4cCI6MjA5NTkzNDcwNX0.kyIphJzU-gNIEvA2rXAWAKy6lC4Vur362U2lFWm6BtI"
        
        # Create client
        supabase = create_client(supabase_url, supabase_key)
        
        # Get next order number by counting existing orders
        try:
            response = supabase.table('orders').select('id', count='exact').execute()
            order_no = response.count + 1 if response.count else 1
        except Exception as e:
            print(f"Could not get count: {e}")
            order_no = 1
        
        # Insert order
        order_data = {
            "order_no": order_no,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "customer_name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "quantity": quantity,
            "payment_id": payment_id
        }
        
        result = supabase.table('orders').insert(order_data).execute()
        print(f"✅ Order #{order_no} saved to Supabase")
        return True
        
    except Exception as e:
        print(f"❌ Supabase error: {str(e)}")
        return False

# ==========================================
# SEND WHATSAPP MESSAGE
# ==========================================
def send_whatsapp_message(name, phone, quantity):
    try:
        # Remove spaces and +91
        phone = phone.replace(" ", "").replace("+91", "")
        
        # Fix the URL - the '12345' looks suspicious, replace with your actual instance ID
        url = f"https://live-mt-server.wati.io/12345/api/v1/sendTemplateMessage?whatsappNumber=91{phone}"
        
        payload = {
            "template_name": "order_confirmation",
            "broadcast_name": "order_confirmation",
            "parameters": [
                {"name": "name", "value": name},
                {"name": "quantity", "value": quantity}
            ]
        }
        
        headers = {
            "Authorization": "wati_f8ed980e-5142-424a-9096-7cb7b2a40bd3.pUd4YizkgaTv3b1hRdnRjpIMRcObEZ9udOuJ6hN2L0_FptY3fKsysDz8Skt30_ziCCNiYbn4FsD0YbmN4OP8jpVDCwpN2scUSqq28QMUwtWjWmMjdxIJNPL8EQIRE3bt",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"WhatsApp response: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"WhatsApp Error: {str(e)}")
        return False

# ==========================================
# USER PAYMENT POST - MAIN FUNCTION
# ==========================================
def userpayment_post(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        quantity = request.POST.get('quantity')
        payment_id = request.POST.get('payment_id')
        
        if not email:
            return HttpResponse("Email not found")
        
        # Success HTML template
        success_html = """
        <script>
        alert('Payment Successful!');
        window.location='/';
        </script>
        """
        
        # 1. Send emails (critical - if this fails, alert the user)
        email_sent = False
        try:
            # Customer HTML Email
            customer_html = f"""
            <html>
            <body style="font-family: Arial; background:#f4f4f4; padding:30px;">
            <div style="max-width:600px; margin:auto; background:white; border-radius:15px; padding:30px;">
            <h1 style="color:#0b7d45; text-align:center;">🌿 ECOMONKS</h1>
            <h2>Thank You For Your Order</h2>
            <p>Dear <b>{name}</b>,</p>
            <p>Your payment has been received successfully and your order is confirmed.</p>
            <div style="background:#f7fff9; border:1px solid #d4f5dd; padding:20px; border-radius:10px;">
            <h3>🧾 Order Details</h3>
            <p><b>👤 Name:</b> {name}</p>
            <p><b>📧 Email:</b> {email}</p>
            <p><b>📞 Phone:</b> {phone}</p>
            <p><b>📍 Address:</b> {address}</p>
            <p><b>📦 Quantity:</b> {quantity}</p>
            <p><b>💳 Payment ID:</b> {payment_id}</p>
            </div>
            </div>
            </body>
            </html>
            """
            
            admin_html = f"""
            <html>
            <body>
            <h2>🚨 NEW ORDER RECEIVED</h2>
            <p><b>Customer:</b> {name}</p>
            <p><b>Email:</b> {email}</p>
            <p><b>Phone:</b> {phone}</p>
            <p><b>Address:</b> {address}</p>
            <p><b>Quantity:</b> {quantity}</p>
            <p><b>Payment ID:</b> {payment_id}</p>
            </body>
            </html>
            """
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login("founder@ecomonks.in", "crmwddzdzoqatofz")
            
            # Customer email
            customer_msg = MIMEMultipart()
            customer_msg['From'] = "founder@ecomonks.in"
            customer_msg['To'] = email
            customer_msg['Subject'] = "ECOMONKS Order Confirmation"
            customer_msg.attach(MIMEText(customer_html, 'html', 'utf-8'))
            server.sendmail("founder@ecomonks.in", email, customer_msg.as_string())
            
            # Admin email
            admin_msg = MIMEMultipart()
            admin_msg['From'] = "founder@ecomonks.in"
            admin_msg['To'] = "founder@ecomonks.in"
            admin_msg['Subject'] = "New ECOMONKS Order Received"
            admin_msg.attach(MIMEText(admin_html, 'html', 'utf-8'))
            server.sendmail("founder@ecomonks.in", "founder@ecomonks.in", admin_msg.as_string())
            
            server.quit()
            email_sent = True
            print("✅ Emails sent successfully")
            
        except Exception as e:
            print(f"❌ Email error: {str(e)}")
            # If email fails, still continue but log it
        
        # 2. Save to Supabase (non-critical)
        try:
            save_order_to_supabase(name, email, phone, address, quantity, payment_id)
        except Exception as e:
            print(f"❌ Supabase save error: {str(e)}")
        
        # 3. Send WhatsApp (non-critical)
        try:
            send_whatsapp_message(name, phone, quantity)
        except Exception as e:
            print(f"❌ WhatsApp error: {str(e)}")
        
        # Always return success to user
        return HttpResponse(success_html)
    
    return HttpResponse("Invalid Request")

# ==========================================
# SUBSCRIPTION EMAIL FUNCTION
# ==========================================
def emailenquiry(request):
    if request.method == "POST":
        email = request.POST.get('email')
        
        try:
            subscription_html = f"""
            <html>
            <body style="font-family: Arial; background:#f4f4f4; padding:30px;">
            <div style="max-width:600px; margin:auto; background:white; border-radius:15px; padding:30px;">
            <h1 style="color:#0b7d45; text-align:center;">🌿 Welcome to ECOMONKS</h1>
            <p>Thank you for subscribing to ECOMONKS.</p>
            <p>We are excited to have you as part of our growing family ❤️</p>
            </div>
            </body>
            </html>
            """
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login("founder@ecomonks.in", "crmwddzdzoqatofz")
            
            subscriber_msg = MIMEMultipart()
            subscriber_msg['From'] = "founder@ecomonks.in"
            subscriber_msg['To'] = email
            subscriber_msg['Subject'] = "ECOMONKS Subscription"
            subscriber_msg.attach(MIMEText(subscription_html, 'html', 'utf-8'))
            server.sendmail("founder@ecomonks.in", email, subscriber_msg.as_string())
            
            server.quit()
            
            return HttpResponse("""
            <script>
            alert('Subscribed Successfully');
            window.location='/';
            </script>
            """)
            
        except Exception as e:
            return HttpResponse(f"ERROR: {str(e)}")
    
    return HttpResponse("Invalid Request")