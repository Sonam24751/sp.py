import streamlit as st
import mysql.connector
import random
from datetime import datetime
import pandas as pd
import base64
import smtplib
from email.message import EmailMessage

# ---------- Email OTP Helpers ----------
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(email, otp):
    msg = EmailMessage()
    msg['Subject'] = 'Your Attendance OTP Verification'
    msg['From'] = 'gauravkashyapnstik@gmail.com'
    msg['To'] = email
    msg.set_content(f'Your OTP is: {otp}')
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('gauravkashyapnstik@gmail.com', 'klmplzmyqisjkmtm')
            smtp.send_message(msg)
        return True
    except Exception as e:
        print("Email error:", e)
        return False

# ---------- Background Styling ----------
def set_bg_from_local(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(f"""<style>.stApp {{
        background: linear-gradient(rgba(255,255,255,0.7), rgba(255,255,255,0.3)),
        url("data:image/jpg;base64,{encoded}") no-repeat center center fixed;
        background-size: cover; }}</style>""", unsafe_allow_html=True)

def set_admin_bg(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(f"""<style>.stApp {{
        background: url("data:image/jpg;base64,{encoded}") no-repeat center center fixed;
        background-size: cover; }}</style>""", unsafe_allow_html=True)

# ---------- DB Connection ----------
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root24',
    database='attendence'
)
cursor = conn.cursor()

# ---------- Functions ----------
def generate_user_id():
    return str(random.randint(1000, 9999))

def register_user(name, department, role, email, photo_bytes):
    user_id = generate_user_id()
    while True:
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            break
        user_id = generate_user_id()
    photo_b64 = base64.b64encode(photo_bytes).decode() if photo_bytes else None
    cursor.execute("""
        INSERT INTO users (user_id, name, department, role, email, photo)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, name, department, role, email, photo_b64))
    conn.commit()
    return user_id

def update_user(user_id, name, department, role, email, photo_bytes):
    photo_b64 = base64.b64encode(photo_bytes).decode() if photo_bytes else None
    if photo_b64:
        cursor.execute("""
            UPDATE users
            SET name = %s, department = %s, role = %s, email = %s, photo = %s
            WHERE user_id = %s
        """, (name, department, role, email, photo_b64, user_id))
    else:
        cursor.execute("""
            UPDATE users
            SET name = %s, department = %s, role = %s, email = %s
            WHERE user_id = %s
        """, (name, department, role, email, user_id))
    conn.commit()

def admin_login(name, password):
    cursor.execute("SELECT password FROM admin WHERE name = %s", (name,))
    result = cursor.fetchone()
    return result and result[0] == password

def check_today_login(user_id):
    today = datetime.now().date()
    cursor.execute(""" 
        SELECT * FROM attendance
        WHERE user_id = %s AND DATE(timestamp) = %s AND status = 'Present'
        ORDER BY timestamp DESC LIMIT 1
    """, (user_id, today))
    return cursor.fetchone()

def get_user_photo(user_id):
    cursor.execute("SELECT photo FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def mark_login(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        return False, None
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO attendance (user_id, name, department, role, status, timestamp)
        VALUES (%s, %s, %s, %s, 'Present', %s)
    """, (user[0], user[1], user[2], user[3], now))
    conn.commit()
    return True, user[1]

def mark_logout(user_id):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    if user:
        cursor.execute("""
            INSERT INTO attendance (user_id, name, department, role, status, timestamp)
            VALUES (%s, %s, %s, %s, 'Logout', %s)
        """, (user[0], user[1], user[2], user[3], now))
        conn.commit()

# ---------- App ----------
st.title("User Attendance System")

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "otp_verified" not in st.session_state:
    st.session_state.otp_verified = False
if "sent_otp" not in st.session_state:
    st.session_state.sent_otp = None
if "reg_otp" not in st.session_state:
    st.session_state.reg_otp = None
if "reg_email" not in st.session_state:
    st.session_state.reg_email = None
if "reg_otp_verified" not in st.session_state:
    st.session_state.reg_otp_verified = False

main_menu = st.sidebar.selectbox("Choose a Login Option", ["👨‍🎓 Student Login", "🛡️ Admin Login"])

# ---------- Admin Login ----------
if main_menu == "🛡️ Admin Login":
    set_admin_bg("register.jpg")
    if not st.session_state.admin_logged_in:
        st.subheader("Admin Login")
        name = st.text_input("Admin Name")
        password = st.text_input("Password", type="password")
        if st.button("Login as Admin"):
            if admin_login(name, password):
                st.session_state.admin_logged_in = True
                st.success("Admin login successful!")
            else:
                st.error("Invalid credentials.")
    else:
        admin_menu = st.sidebar.selectbox("Admin Menu", ["➕ Register New User", "✏️ Update User", "📊 View Attendance", "📋 View Students", "📚 View Faculty", "🚪 Logout"])
        
        if admin_menu == "➕ Register New User":
            set_admin_bg("register.jpg")
            st.subheader("Register New User")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                photo = st.file_uploader("Upload Photo", type=["jpg", "jpeg", "png"])
                if st.button("Send OTP to Email"):
                    if email:
                        otp = generate_otp()
                        st.session_state.reg_otp = otp
                        st.session_state.reg_email = email
                        if send_otp(email, otp):
                            st.success(f"OTP sent to {email}.")
                        else:
                            st.error("Failed to send OTP.")
                    else:
                        st.warning("Please enter an email to send OTP.")

            with col2:
                dept = st.text_input("Department")
            role = st.selectbox("Select Role", ["Student", "Faculty"])

            otp_input = st.text_input("Enter OTP sent to email")
            if st.button("Verify OTP"):
                if otp_input == st.session_state.reg_otp and email == st.session_state.reg_email:
                    st.session_state.reg_otp_verified = True
                    st.success("OTP verified! You can now register the user.")
                else:
                    st.error("Invalid OTP or email mismatch.")

            if st.button("Register"):
                if not st.session_state.reg_otp_verified:
                    st.warning("Please verify OTP first.")
                elif name and dept and email:
                    photo_bytes = photo.read() if photo else None
                    uid = register_user(name, dept, role, email, photo_bytes)
                    st.success(f"User registered successfully! User ID: {uid}")
                    
                    # Send registration details to the user's email
                    msg = EmailMessage()
                    msg['Subject'] = 'Registration Successful'
                    msg['From'] = 'gauravkashyapnstik@gmail.com'
                    msg['To'] = email
                    photo_note = 'Photo uploaded.' if photo_bytes else 'No photo uploaded.'
                    msg.set_content(f"""
Hello {name},

You have been successfully registered to the Attendance System.

Here are your details:
User ID: {uid}
Name: {name}
Department: {dept}
Role: {role}
{photo_note}

Date of Registration: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Regards,
Admin Team
""")
                    try:
                        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                            smtp.login('gauravkashyapnstik@gmail.com', 'klmplzmyqisjkmtm')
                            smtp.send_message(msg)
                        st.info(f"Registration details sent to {email}.")
                    except Exception as e:
                        st.error(f"Failed to send registration email: {e}")
                    
                    # Reset registration OTP state
                    st.session_state.reg_otp_verified = False
                    st.session_state.reg_otp = None
                    st.session_state.reg_email = None
                else:
                    st.warning("Please fill in all fields and verify OTP.")

        elif admin_menu == "✏️ Update User":
            set_admin_bg("register.jpg")
            st.subheader("Update User Details")
            uid = st.text_input("Enter User ID to update")
            if st.button("Fetch User Details"):
                if uid:
                    cursor.execute("SELECT name, department, role, email FROM users WHERE user_id = %s", (uid,))
                    user = cursor.fetchone()
                    if user:
                        st.session_state.update_user = {
                            "user_id": uid,
                            "name": user[0],
                            "department": user[1],
                            "role": user[2],
                            "email": user[3]
                        }
                        st.success("User details loaded. You can now update the fields.")
                    else:
                        st.error("User not found.")
                else:
                    st.warning("Please enter a User ID.")

            if "update_user" in st.session_state:
                update_user_data = st.session_state.update_user
                new_name = st.text_input("Full Name", value=update_user_data["name"])
                new_email = st.text_input("Email", value=update_user_data["email"])
                new_dept = st.text_input("Department", value=update_user_data["department"])
                new_role = st.selectbox("Select Role", ["Student", "Faculty"], index=0 if update_user_data["role"] == "Student" else 1)
                new_photo = st.file_uploader("Upload New Photo (optional)", type=["jpg", "jpeg", "png"])

                if st.button("Update User"):
                    if new_name and new_dept and new_email:
                        photo_bytes = new_photo.read() if new_photo else None
                        update_user(uid, new_name, new_dept, new_role, new_email, photo_bytes)
                        st.success("User details updated successfully.")
                        del st.session_state.update_user
                    else:
                        st.warning("Please fill in all fields.")

        elif admin_menu == "📊 View Attendance":
            set_admin_bg("Attandence.jpg")
            st.subheader("Attendance Records with Login, Logout, Duration")
            cursor.execute("SELECT user_id, name, department, role, status, timestamp FROM attendance ORDER BY user_id, timestamp")
            rows = cursor.fetchall()
            sessions, temp = [], {}
            for row in rows:
                uid, name, dept, role, status, ts = row
                if status == 'Present':
                    temp[uid] = {"User ID": uid, "Name": name, "Department": dept, "Role": role, "Login Time": ts}
                elif status == 'Logout' and uid in temp:
                    session = temp.pop(uid)
                    session["Logout Time"] = ts
                    in_time = datetime.strptime(str(session["Login Time"]), "%Y-%m-%d %H:%M:%S")
                    out_time = datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S")
                    duration = out_time - in_time
                    session["Stay Duration"] = f"{int(duration.total_seconds()//3600)}h {int(duration.total_seconds()%3600//60)}m"
                    sessions.append(session)
            if sessions:
                df = pd.DataFrame(sessions)
                st.dataframe(df, use_container_width=True, height=400)
                st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode('utf-8'), "attendance_records.csv", "text/csv")
            else:
                st.info("No complete session records yet.")
            st.subheader("🟡 Ongoing Sessions")
            ongoing = [s for s in temp.values()]
            for s in ongoing:
                s.update({"Logout Time": "—", "Stay Duration": "Ongoing"})
            if ongoing:
                st.dataframe(pd.DataFrame(ongoing), use_container_width=True, height=300)

        elif admin_menu == "📋 View Students":
            set_admin_bg("students.jpg")
            st.subheader("All Students")
            cursor.execute("SELECT user_id, name, department, role, email FROM users WHERE role = 'Student'")
            students = cursor.fetchall()
            if students:
                df = pd.DataFrame(students, columns=["User ID", "Name", "Department", "Role", "Email"])
                st.dataframe(df, use_container_width=True, height=400)
                st.download_button("⬇️ Download Student Data", df.to_csv(index=False).encode('utf-8'), "students_data.csv", "text/csv")
            else:
                st.info("No students found.")

        elif admin_menu == "📚 View Faculty":
            set_admin_bg("students.jpg")
            st.subheader("All Faculty Members")
            cursor.execute("SELECT user_id, name, department, role, email FROM users WHERE role = 'Faculty'")
            faculty = cursor.fetchall()
            if faculty:
                df = pd.DataFrame(faculty, columns=["User ID", "Name", "Department", "Role", "Email"])
                st.dataframe(df, use_container_width=True, height=400)
                st.download_button("⬇️ Download Faculty Data", df.to_csv(index=False).encode('utf-8'), "faculty_data.csv", "text/csv")
            else:
                st.info("No faculty members found.")

        elif admin_menu == "🚪 Logout":
            st.session_state.admin_logged_in = False
            st.success("Logged out successfully.")

# ---------- Student Login ----------
elif main_menu == "👨‍🎓 Student Login":
    set_bg_from_local("unnamed.jpg")
    st.subheader("Student Attendance")
    sid = st.text_input("Enter your 4-digit User ID")
    if sid:
        cursor.execute("SELECT email FROM users WHERE user_id = %s", (sid,))
        data = cursor.fetchone()
        if not data:
            st.error("Invalid User ID.")
        else:
            email = data[0]
            if st.button("Send OTP"):
                otp = generate_otp()
                st.session_state.sent_otp = otp
                if send_otp(email, otp):
                    st.success(f"OTP sent to {email}.")
                else:
                    st.error("Failed to send OTP.")
            otp_input = st.text_input("Enter the OTP")
            if st.button("Verify OTP"):
                if otp_input == st.session_state.sent_otp:
                    st.session_state.otp_verified = True
                    st.success("OTP verified!")
                else:
                    st.error("Incorrect OTP.")
            if st.session_state.otp_verified:
                if st.button("Mark Attendance"):
                    if check_today_login(sid):
                        st.warning("You have already marked your attendance today.")
                    else:
                        success, name = mark_login(sid)
                        if success:
                            st.success(f"Attendance marked successfully for {name}.")
                            photo_b64 = get_user_photo(sid)
                            if photo_b64:
                                st.image(base64.b64decode(photo_b64), caption=f"Photo of {name}", use_column_width=True)
                        else:
                            st.error("Failed to mark attendance. Please try again.")
                if st.button("Logout"):
                    mark_logout(sid)
                    st.success("Logged out successfully.")