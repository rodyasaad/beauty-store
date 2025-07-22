from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from werkzeug.utils import secure_filename
import gspread
from google.oauth2.service_account import Credentials
from flask import jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # يجب تغييرها لاحقًا

# مسارات ملفات البيانات
PRODUCTS_FILE = 'data/products.json'
SITE_INFO_FILE = 'data/site_info.json'
CONFIG_FILE = 'config.json'
GOOGLE_SHEETS_FILE = 'data/google_sheets.json'

# دالة مساعدة لقراءة ملف JSON

def read_json(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# دالة مساعدة لكتابة ملف JSON

def write_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_gs_settings():
    # إذا كان على Vercel أو متغيرات البيئة موجودة
    creds = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "")
    sheet_name = os.environ.get("GOOGLE_SHEET_NAME", "")
    # إذا كانت جميع القيم موجودة وغير فارغة
    if creds and sheet_id and sheet_name:
        return {
            "service_account_json": creds,
            "sheet_id": sheet_id,
            "sheet_name": sheet_name
        }
    # إذا كانت متغيرات البيئة ناقصة أو فارغة، استخدم ملف google_sheets.json
    return read_json(GOOGLE_SHEETS_FILE)

def write_gs_settings(data):
    write_json(GOOGLE_SHEETS_FILE, data)

def get_gs_client(settings):
    creds_dict = settings.get('service_account_json')
    if not creds_dict:
        raise Exception('بيانات الاعتماد غير موجودة')
    import json as _json
    creds = Credentials.from_service_account_info(_json.loads(creds_dict), scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

# دالة تحقق من تسجيل الدخول

def is_logged_in():
    return session.get('admin_logged_in')

def require_login():
    if not is_logged_in():
        return redirect(url_for('admin_login'))

def is_vercel():
    return os.environ.get("GOOGLE_SHEETS_CREDENTIALS") is not None

def get_all_products():
    if is_vercel():
        settings = read_gs_settings()
        client = get_gs_client(settings)
        sheet = client.open_by_key(settings['sheet_id'])
        ws = sheet.worksheet(settings['sheet_name'])
        rows = ws.get_all_records()
        return rows
    else:
        return read_json(PRODUCTS_FILE).get('products', [])

def save_all_products(products):
    if is_vercel():
        settings = read_gs_settings()
        client = get_gs_client(settings)
        sheet = client.open_by_key(settings['sheet_id'])
        ws = sheet.worksheet(settings['sheet_name'])
        header = ['id', 'name', 'description', 'price', 'image', 'whatsapp', 'category']
        data = [header]
        for p in products:
            data.append([
                p.get('id', ''),
                p.get('name', ''),
                p.get('description', ''),
                p.get('price', ''),
                p.get('image', ''),
                p.get('whatsapp', ''),
                p.get('category', '')
            ])
        ws.clear()
        ws.update('A1', data)
    else:
        write_json(PRODUCTS_FILE, {'products': products})

def get_all_banners():
    if is_vercel():
        settings = read_gs_settings()
        client = get_gs_client(settings)
        sheet = client.open_by_key(settings['sheet_id'])
        try:
            ws = sheet.worksheet('banners')
        except Exception:
            ws = sheet.add_worksheet(title='banners', rows=1, cols=50)
        # استرجع كل القيم من العمود الأول كسطر واحد
        banners = ws.col_values(1)
        return banners
    else:
        site_info = read_json(SITE_INFO_FILE)
        return site_info.get('banner_images', [])

def save_all_banners(banner_images):
    if is_vercel():
        settings = read_gs_settings()
        client = get_gs_client(settings)
        sheet = client.open_by_key(settings['sheet_id'])
        try:
            ws = sheet.worksheet('banners')
        except Exception:
            ws = sheet.add_worksheet(title='banners', rows=1, cols=50)
        ws.clear()
        if banner_images:
            ws.update('A1', [[img] for img in banner_images])
    else:
        site_info = read_json(SITE_INFO_FILE)
        site_info['banner_images'] = banner_images
        write_json(SITE_INFO_FILE, site_info)

def get_site_info():
    if is_vercel():
        settings = read_gs_settings()
        client = get_gs_client(settings)
        sheet = client.open_by_key(settings['sheet_id'])
        sheet_name = settings.get('sheet_name', 'Sheet1') or 'Sheet1'
        try:
            ws = sheet.worksheet(sheet_name)
        except Exception:
            ws = sheet.add_worksheet(title=sheet_name, rows=12, cols=2)
            ws.update('A1:B10', [["key", "value"],
                                 ["site_name", ""],
                                 ["description", ""],
                                 ["whatsapp", ""],
                                 ["instagram", ""],
                                 ["tiktok", ""],
                                 ["email", ""],
                                 ["about", ""],
                                 ["policy", ""],
                                 ["currency", ""]])
        values = ws.get_all_values()
        site_info = {}
        for row in values[1:]:
            if len(row) >= 2:
                site_info[row[0]] = row[1]
        return site_info
    else:
        return read_json(SITE_INFO_FILE)

def save_site_info(site_info):
    if is_vercel():
        settings = read_gs_settings()
        client = get_gs_client(settings)
        sheet = client.open_by_key(settings['sheet_id'])
        sheet_name = settings.get('sheet_name', 'Sheet1') or 'Sheet1'
        try:
            ws = sheet.worksheet(sheet_name)
        except Exception:
            ws = sheet.add_worksheet(title=sheet_name, rows=12, cols=2)
            ws.update('A1:B10', [["key", "value"],
                                 ["site_name", ""],
                                 ["description", ""],
                                 ["whatsapp", ""],
                                 ["instagram", ""],
                                 ["tiktok", ""],
                                 ["email", ""],
                                 ["about", ""],
                                 ["policy", ""],
                                 ["currency", ""]])
        # تحديث القيم في العمود B حسب المفاتيح في العمود A
        values = ws.get_all_values()
        keys = [row[0] for row in values[1:]]
        for i, key in enumerate(keys, start=2):
            ws.update(f'B{i}', site_info.get(key, ""))
    else:
        write_json(SITE_INFO_FILE, site_info)

# عدل دالة index
@app.route('/')
def index():
    products = get_all_products()
    site_info = get_site_info()
    categories = list({p.get('category', 'غير مصنف') for p in products})
    categories_with_products = [cat for cat in categories if cat != 'غير مصنف' and any(p.get('category') == cat for p in products)]
    banners = []
    for img in get_all_banners():
        banners.append({'image_url': img})
    return render_template('index.html', products=products, site_info=site_info, categories=categories, categories_with_products=categories_with_products, banners=banners)

# صفحة تسجيل الدخول
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if is_logged_in():
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        config = read_json(CONFIG_FILE)
        username = request.form['username']
        password = request.form['password']
        if username == config.get('admin_username') and password == config.get('admin_password'):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('بيانات الدخول غير صحيحة')
    return render_template('login.html')

# تسجيل الخروج
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# لوحة التحكم الرئيسية (تحويل للمنتجات)
@app.route('/admin')
def admin_dashboard():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    return redirect(url_for('admin_products'))

# إدارة المنتجات
@app.route('/admin/products')
def admin_products():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    products = get_all_products()
    return render_template('admin_products.html', products=products)

# إضافة منتج
@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    products = get_all_products()
    categories = list({p.get('category', 'غير مصنف') for p in products})
    if request.method == 'POST':
        required_fields = ['name', 'description', 'price', 'whatsapp', 'image']
        for field in required_fields:
            if not request.form.get(field):
                flash('جميع الحقول مطلوبة!')
                return render_template('admin_product_form.html', product=None, categories=categories)
        new_id = max([int(p['id']) for p in products if str(p.get('id', '')).isdigit()], default=0) + 1
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        whatsapp = request.form['whatsapp']
        category = request.form.get('new_category') or request.form.get('category') or 'غير مصنف'
        image_path = request.form['image']
        new_product = {
            'id': new_id,
            'name': name,
            'description': description,
            'price': price,
            'whatsapp': whatsapp,
            'image': image_path,
            'category': category
        }
        try:
            products.append(new_product)
            save_all_products(products)
            flash('تم حفظ المنتج بنجاح!')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash(f'حدث خطأ أثناء حفظ المنتج: {e}')
            return render_template('admin_product_form.html', product=None, categories=categories)
    return render_template('admin_product_form.html', product=None, categories=categories)

# تعديل منتج
@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    products = get_all_products()
    categories = list({p.get('category', 'غير مصنف') for p in products})
    product = next((p for p in products if int(p['id']) == product_id), None)
    if not product:
        return redirect(url_for('admin_products'))
    if request.method == 'POST':
        required_fields = ['name', 'description', 'price', 'whatsapp', 'image']
        for field in required_fields:
            if not request.form.get(field):
                flash('جميع الحقول مطلوبة!')
                return render_template('admin_product_form.html', product=product, categories=categories)
        product['name'] = request.form['name']
        product['description'] = request.form['description']
        product['price'] = request.form['price']
        product['whatsapp'] = request.form['whatsapp']
        category = request.form.get('new_category') or request.form.get('category') or 'غير مصنف'
        product['category'] = category
        product['image'] = request.form['image']
        save_all_products(products)
        return redirect(url_for('admin_products'))
    return render_template('admin_product_form.html', product=product, categories=categories)

# حذف منتج
@app.route('/admin/products/delete/<int:product_id>')
def admin_delete_product(product_id):
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    products = get_all_products()
    products = [p for p in products if int(p['id']) != product_id]
    save_all_products(products)
    return redirect(url_for('admin_products'))

# تعديل البنر
@app.route('/admin/banner', methods=['GET', 'POST'])
def admin_banner():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    site_info = read_json(SITE_INFO_FILE)
    if request.method == 'POST':
        try:
            banner_images = request.form.getlist('banner_images')
            save_all_banners(banner_images)
            flash('تم حفظ البنرات بنجاح!')
            return redirect(url_for('admin_banner'))
        except Exception as e:
            flash(f'حدث خطأ أثناء حفظ البنرات: {e}')
            site_info['banner_images'] = get_all_banners()
            return render_template('admin_banner.html', site_info=site_info)
    site_info['banner_images'] = get_all_banners()
    return render_template('admin_banner.html', site_info=site_info)

# تعديل معلومات الموقع
@app.route('/admin/site-info', methods=['GET', 'POST'])
def admin_site_info():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    site_info = get_site_info()
    if request.method == 'POST':
        site_info['site_name'] = request.form.get('site_name', '')
        site_info['description'] = request.form.get('description', '')
        site_info['whatsapp'] = request.form.get('whatsapp', '')
        site_info['instagram'] = request.form.get('instagram', '')
        site_info['tiktok'] = request.form.get('tiktok', '')
        site_info['email'] = request.form.get('email', '')
        site_info['about'] = request.form.get('about', '')
        site_info['policy'] = request.form.get('policy', '')
        site_info['currency'] = request.form.get('currency', '')
        try:
            save_site_info(site_info)
            print('تم حفظ معلومات الموقع بنجاح')
            flash('تم حفظ معلومات الموقع بنجاح!')
            return redirect(url_for('admin_site_info'))
        except Exception as e:
            error_message = f'حدث خطأ أثناء حفظ معلومات الموقع: {e}'
            return render_template('admin_site_info.html', site_info=site_info, error_message=error_message)
    return render_template('admin_site_info.html', site_info=site_info)

@app.route('/admin/google-sheets', methods=['GET', 'POST'])
def admin_google_sheets():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    message = None
    settings = read_gs_settings()
    if request.method == 'POST':
        settings['sheet_id'] = request.form['sheet_id']
        settings['sheet_name'] = request.form['sheet_name']
        settings['service_account_json'] = request.form['service_account_json']
        write_gs_settings(settings)
        message = 'تم حفظ الإعدادات بنجاح.'
    return render_template('admin_google_sheets.html', settings=settings, message=message)

@app.route('/admin/google-sheets/test', methods=['POST'])
def admin_google_sheets_test():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    settings = read_gs_settings()
    try:
        client = get_gs_client(settings)
        sheet = client.open_by_key(settings['sheet_id'])
        ws = sheet.worksheet(settings['sheet_name'])
        ws.get_all_records()
        message = 'تم الاتصال بنجاح!'
    except Exception as e:
        message = f'فشل الاتصال: {e}'
    return render_template('admin_google_sheets.html', settings=settings, message=message)

@app.route('/admin/google-sheets/import', methods=['POST'])
def admin_google_sheets_import():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    settings = read_gs_settings()
    try:
        client = get_gs_client(settings)
        sheet = client.open_by_key(settings['sheet_id'])
        ws = sheet.worksheet(settings['sheet_name'])
        rows = ws.get_all_records()
        products = []
        for row in rows:
            products.append({
                'id': int(row.get('id', 0)),
                'name': row.get('name', ''),
                'description': row.get('description', ''),
                'price': row.get('price', ''),
                'image': row.get('image', ''),
                'whatsapp': row.get('whatsapp', ''),
                'category': row.get('category', '')
            })
        # فقط احفظ في ملف JSON إذا لم تكن على Vercel
        if not is_vercel():
            write_json(PRODUCTS_FILE, {'products': products})
        message = f'تم استيراد {len(products)} منتج من Google Sheets.'
    except Exception as e:
        message = f'فشل الاستيراد: {e}'
    return render_template('admin_google_sheets.html', settings=settings, message=message)

@app.route('/admin/google-sheets/export', methods=['POST'])
def admin_google_sheets_export():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    settings = read_gs_settings()
    try:
        client = get_gs_client(settings)
        sheet = client.open_by_key(settings['sheet_id'])
        ws = sheet.worksheet(settings['sheet_name'])
        products = read_json(PRODUCTS_FILE).get('products', [])
        # تجهيز البيانات
        header = ['id', 'name', 'description', 'price', 'image', 'whatsapp', 'category']
        data = [header]
        for p in products:
            data.append([
                p.get('id', ''),
                p.get('name', ''),
                p.get('description', ''),
                p.get('price', ''),
                p.get('image', ''),
                p.get('whatsapp', ''),
                p.get('category', '')
            ])
        ws.clear()
        ws.update('A1', data)
        message = f'تم تصدير {len(products)} منتج إلى Google Sheets.'
    except Exception as e:
        message = f'فشل التصدير: {e}'
    return render_template('admin_google_sheets.html', settings=settings, message=message)

# عدل دالة products_page
@app.route('/products')
def products_page():
    products = get_all_products()
    site_info = get_site_info()
    categories = list({p.get('category', 'غير مصنف') for p in products})
    return render_template('products.html', products=products, site_info=site_info, categories=categories, selected_category=None)

if __name__ == '__main__':
    app.run(debug=True) 
