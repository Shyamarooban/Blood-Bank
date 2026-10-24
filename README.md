# Blood Bank Management System — Flask + MySQL

## Install and run
1. Install Python 3.10+ and XAMPP (or MySQL). Start **MySQL** in XAMPP; Apache is not required for Flask.
2. Open `http://localhost/phpmyadmin`, select Import, choose `schema.sql` from this folder, and click Go.
3. Defaults in `app.py` and `create_admin.py`: host `127.0.0.1`, user `root`, blank password, database `blood_bank_db`. Change if your local MySQL credentials differ.
4. Open a terminal in this folder and run:

Windows Command Prompt:
```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
```
PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```
5. Create your login: `python create_admin.py`. Choose username and password (at least 8 characters).
6. Start the site: `python app.py`
7. Open `http://127.0.0.1:5000` in your browser. Keep the terminal open; Ctrl+C stops Flask.

## Features
Login, dashboard, person registration, donation records, requests, and blood stock.
Donations add quantity to the donor's blood group. Approved requests check availability and reduce stock. Pending requests do not change stock.

## ER mapping
USER -> users; PERSON -> persons; DONATION -> donations; RECEIVE -> receives; STOCK -> blood_stock.
Foreign keys connect donations and requests to persons.

Academic demo only: no eligibility, testing, expiry, or clinical compatibility validation. Flask's development server is for local use only.
