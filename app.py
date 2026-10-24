import os
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-local-development-key")
DB = dict(host=os.getenv("DB_HOST","127.0.0.1"), user=os.getenv("DB_USER","root"),
          password=os.getenv("DB_PASSWORD",""), database=os.getenv("DB_NAME","blood_bank_db"))
GROUPS = ["A+","A-","B+","B-","AB+","AB-","O+","O-"]
GENDERS = ["Male","Female","Other"]

def connect():
    return mysql.connector.connect(**DB)

def rows(sql, params=()):
    cn=connect()
    try:
        cur=cn.cursor(dictionary=True); cur.execute(sql,params); return cur.fetchall()
    finally:
        cur.close(); cn.close()

def row(sql, params=()):
    result=rows(sql,params)
    return result[0] if result else {}

def guard():
    if "user_id" not in session: return redirect(url_for("login"))
    return None

@app.route("/")
def home():
    return redirect(url_for("dashboard" if session.get("user_id") else "login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if session.get("user_id"): return redirect(url_for("dashboard"))
    if request.method=="POST":
        try:
            u=row("SELECT user_id,username,user_password FROM users WHERE username=%s",(request.form.get("username","").strip(),))
            if u and check_password_hash(u["user_password"],request.form.get("password","")):
                session.clear(); session["user_id"]=u["user_id"]; session["username"]=u["username"]
                return redirect(url_for("dashboard"))
            flash("Invalid username or password.","error")
        except Error:
            flash("Database connection failed. Check MySQL and database settings.","error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    g=guard()
    if g:return g
    try:
        stats={"persons":row("SELECT COUNT(*) n FROM persons")["n"],"donations":row("SELECT COUNT(*) n FROM donations")["n"],"requests":row("SELECT COUNT(*) n FROM receives")["n"],"stock":row("SELECT COALESCE(SUM(quantity_ml),0) n FROM blood_stock")["n"]}
        stock=rows("SELECT * FROM blood_stock ORDER BY FIELD(blood_group,'O-','O+','A-','A+','B-','B+','AB-','AB+')")
        recent=rows("SELECT d.*,p.name,p.blood_group FROM donations d JOIN persons p ON p.person_id=d.person_id ORDER BY donation_id DESC LIMIT 5")
    except Error:
        flash("Import schema.sql first, then refresh this page.","error")
        stats={"persons":0,"donations":0,"requests":0,"stock":0};stock=[];recent=[]
    return render_template("dashboard.html",stats=stats,stock=stock,recent=recent)

@app.route("/persons",methods=["GET","POST"])
def persons():
    g=guard()
    if g:return g
    if request.method=="POST":
        f=request.form; name=f.get("name","").strip(); bg=f.get("blood_group",""); gender=f.get("gender","")
        if not name or bg not in GROUPS or gender not in GENDERS: flash("Enter name, blood group and gender correctly.","error")
        else:
            cn=connect();cur=cn.cursor()
            try:
                cur.execute("INSERT INTO persons(name,address,phone,blood_group,gender,date_of_birth,medical_issues) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (name,f.get("address","").strip() or None,f.get("phone","").strip() or None,bg,gender,f.get("date_of_birth") or None,f.get("medical_issues","").strip() or None))
                cn.commit();flash("Person registered successfully.")
            except Error: cn.rollback();flash("Could not save person. Check your entries.","error")
            finally:cur.close();cn.close()
        return redirect(url_for("persons"))
    return render_template("persons.html",persons=rows("SELECT * FROM persons ORDER BY person_id DESC"),groups=GROUPS,genders=GENDERS)

@app.route("/donations",methods=["GET","POST"])
def donations():
    g=guard()
    if g:return g
    if request.method=="POST":
        f=request.form; pid=f.get("person_id",type=int); qty=f.get("quantity_ml",type=int)
        if not pid or not qty or qty<1 or not f.get("donation_date") or not f.get("donation_time"): flash("Enter person, date, time and positive quantity.","error")
        else:
            cn=connect();cur=cn.cursor(dictionary=True)
            try:
                cn.start_transaction();cur.execute("SELECT blood_group FROM persons WHERE person_id=%s FOR UPDATE",(pid,));p=cur.fetchone()
                if not p: raise ValueError()
                cur.execute("INSERT INTO donations(person_id,donation_date,donation_time,quantity_ml) VALUES(%s,%s,%s,%s)",(pid,f["donation_date"],f["donation_time"],qty))
                cur.execute("UPDATE blood_stock SET quantity_ml=quantity_ml+%s WHERE blood_group=%s",(qty,p["blood_group"]))
                cn.commit();flash("Donation saved and stock updated.")
            except (Error,ValueError):cn.rollback();flash("Could not save donation. Check selected person and values.","error")
            finally:cur.close();cn.close()
        return redirect(url_for("donations"))
    return render_template("donations.html",people=rows("SELECT person_id,name,blood_group FROM persons ORDER BY name"),donations=rows("SELECT d.*,p.name,p.blood_group FROM donations d JOIN persons p ON p.person_id=d.person_id ORDER BY donation_id DESC"),today=date.today().isoformat(),now=datetime.now().strftime("%H:%M"))

@app.route("/requests",methods=["GET","POST"])
def receives():
    g=guard()
    if g:return g
    if request.method=="POST":
        f=request.form;pid=f.get("person_id",type=int);qty=f.get("quantity_ml",type=int);hospital=f.get("hospital","").strip();bg=f.get("blood_group","");status=f.get("status","Pending")
        if not pid or not qty or qty<1 or not hospital or not f.get("receive_date") or bg not in GROUPS or status not in ["Pending","Approved"]:flash("Complete all fields with valid values.","error")
        else:
            cn=connect();cur=cn.cursor(dictionary=True)
            try:
                cn.start_transaction();cur.execute("SELECT person_id FROM persons WHERE person_id=%s",(pid,))
                if not cur.fetchone():raise ValueError("person")
                if status=="Approved":
                    cur.execute("SELECT quantity_ml FROM blood_stock WHERE blood_group=%s FOR UPDATE",(bg,));s=cur.fetchone()
                    if not s or s["quantity_ml"]<qty:raise ValueError("stock")
                cur.execute("INSERT INTO receives(person_id,hospital,receive_date,blood_group,quantity_ml,status) VALUES(%s,%s,%s,%s,%s,%s)",(pid,hospital,f["receive_date"],bg,qty,status))
                if status=="Approved":
                    cur.execute("UPDATE blood_stock SET quantity_ml=quantity_ml-%s WHERE blood_group=%s AND quantity_ml>=%s",(qty,bg,qty))
                    if cur.rowcount!=1:raise ValueError("stock")
                cn.commit();flash("Request approved and stock reduced." if status=="Approved" else "Pending request saved; stock unchanged.")
            except ValueError as e:cn.rollback();flash("Insufficient stock; request not saved." if str(e)=="stock" else "Person not found.","error")
            except Error:cn.rollback();flash("Could not save request. Check database and values.","error")
            finally:cur.close();cn.close()
        return redirect(url_for("receives"))
    return render_template("receives.html",people=rows("SELECT person_id,name FROM persons ORDER BY name"),requests=rows("SELECT r.*,p.name FROM receives r JOIN persons p ON p.person_id=r.person_id ORDER BY receive_id DESC"),groups=GROUPS,today=date.today().isoformat())

@app.route("/stock")
def stock_page():
    g=guard()
    if g:return g
    stock=rows("SELECT * FROM blood_stock ORDER BY FIELD(blood_group,'O-','O+','A-','A+','B-','B+','AB-','AB+')")
    return render_template("stock.html",stock=stock,total=sum(x["quantity_ml"] for x in stock))

if __name__=="__main__":
    app.run(debug=True)
