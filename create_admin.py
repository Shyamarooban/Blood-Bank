import os, getpass
import mysql.connector
from werkzeug.security import generate_password_hash
db=dict(host=os.getenv("DB_HOST","127.0.0.1"),user=os.getenv("DB_USER","root"),password=os.getenv("DB_PASSWORD",""),database=os.getenv("DB_NAME","blood_bank_db"))
username=input("Admin username [admin]: ").strip() or "admin"
password=getpass.getpass("Choose password (at least 8 characters): ")
if len(password)<8: raise SystemExit("Password must be at least 8 characters.")
cn=mysql.connector.connect(**db);cur=cn.cursor()
try:
 cur.execute("INSERT INTO users(username,user_password) VALUES(%s,%s)",(username,generate_password_hash(password)));cn.commit();print("Admin account created.")
except mysql.connector.IntegrityError: print("Username already exists; choose another.")
finally:cur.close();cn.close()
