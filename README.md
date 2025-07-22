# متجر إلكتروني بسيط بـ Flask وملفات JSON

## المتطلبات
- Python 3.8+
- Flask

## طريقة التشغيل محليًا

```bash
pip install -r requirements.txt
python app.py
```

## بنية المشروع
- `app.py` : التطبيق الرئيسي
- `data/products.json` : بيانات المنتجات
- `data/site_info.json` : معلومات الموقع
- `config.json` : بيانات الدخول للوحة التحكم
- `static/images/` : صور المنتجات والبنر
- `templates/` : قوالب HTML

## النشر على Vercel
- استخدم [Vercel Python Flask guide](https://vercel.com/guides/deploying-python-with-vercel) مع ملف `requirements.txt` وملف `app.py` في الجذر.

## ملاحظات
- جميع البيانات تُخزن في ملفات JSON فقط.
- لوحة التحكم محمية بكلمة سر بسيطة من `config.json`.
- التصميم يدعم اللغة العربية ويدعم الجوال. 