# Shipping Company — نظام إدارة شركات الشحن

> نظام متكامل لإدارة شركات الشحن والاستيراد والتصدير

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

## 🎯 نظرة عامة

تطبيق سطح مكتب متكامل لإدارة شركات الشحن، مبني بـ **PyQt6** و **SQLAlchemy**. يتضمن النظام 7 وحدات رئيسية تغطي جميع جوانب إدارة شركة الشحن.

## ✨ الميزات الرئيسية

| الوحدة | الميزات |
|--------|---------|
| 💰 **الخزينة** | إدارة الحسابات (صندوق، بنك، CCP)، التحويلات، سجل المعاملات |
| 💱 **العملات** | شراء العملات، إدارة الموردين، التسديدات، أرصدة العملات |
| 👥 **العملاء** | إدارة العملاء، البضائع، التسديدات، المصاريف الجانبية، كشف الحساب |
| 📋 **التراخيص** | أصحاب الرخص، التراخيص، الحسابات البنكية، تحويلات DA |
| 🚢 **اللوجستيك** | وكلاء الشحن، الفواتير/الحاويات، المصاريف، معالج 3 خطوات |
| 🌍 **الديون الخارجية** | جهات الاتصال الخارجية، المعاملات، الأرصدة |
| 🤝 **الشركاء** | إدارة الشركاء، الحسابات، المعاملات |

## 🚀 البدء السريع

### المتطلبات

- Python 3.10+
- Windows / Linux / macOS

### التثبيت

```bash
# استنساخ المستودع
git clone https://github.com/boukhroufatech-rgb/shipping_company.git
cd shipping_company

# إنشاء بيئة افتراضية
python -m venv venv
venv\Scripts\activate  # على Windows
# source venv/bin/activate  # على Linux/Mac

# تثبيت المكتبات
pip install -r requirements.txt

# إنشاء قاعدة البيانات
python create_tables.py

# تشغيل التطبيق
python main.py
```

## 📁 بنية المشروع

```
shipping_company/
├── main.py                    # نقطة الدخول الرئيسية
├── core/                      # النواة (DB, Models, Repositories)
│   ├── database.py            # إدارة قاعدة البيانات
│   ├── models.py              # 21 نموذج (جدول)
│   ├── repositories.py        # طبقة الوصول للبيانات
│   ├── services.py            # خدمات النواة
│   └── themes.py              # 13 ثيم
├── modules/                   # الوحدات الرئيسية (7)
│   ├── treasury/              # الخزينة
│   ├── currency/              # العملات
│   ├── customers/             # العملاء
│   ├── licenses/              # التراخيص
│   ├── logistics/             # اللوجستيك
│   ├── external_debt/         # الديون الخارجية
│   ├── partners/              # الشركاء
│   ├── settings/              # الإعدادات
│   └── documents/             # مولّد المستندات
├── components/                # مكونات واجهة موحدة
│   ├── enhanced_table.py      # الجدول الموحد
│   ├── smart_form.py          # النموذج الذكي
│   └── ...
├── utils/                     # الأدوات المساعدة
│   ├── formatters.py          # تنسيق الأرقام والتواريخ
│   ├── validators.py          # التحقق من البيانات
│   ├── error_handler.py       # معالج الأخطاء
│   └── icon_manager.py        # إدارة الأيقونات
└── assets/                    # الأيقونات والموارد
```

## 🗄️ قاعدة البيانات

يستخدم النظام **SQLite** مع **SQLAlchemy** (ORM). يتضمن 21 جدولاً:

- `currencies`, `exchange_rates` — العملات وأسعار الصرف
- `accounts`, `transactions` — الحسابات والمعاملات
- `customers`, `customer_goods`, `customer_payments` — العملاء
- `import_licenses`, `license_goods` — التراخيص
- `container_files`, `container_expenses` — الحاويات والمصاريف
- `partners`, `partner_transactions` — الشركاء
- `external_contacts`, `external_transactions` — الديون الخارجية

## 🎨 السمات

يوفر التطبيق **13 ثيم** مختلف:

- Emerald, Midnight, Light, Ocean, Sunset
- Forest, Royal, Mono, Cyber, Aurora
- Lavender, Desert, Classic

## 📄 تصدير المستندات

- **PDF**: فواتير، إيصالات، كشوف حساب
- **Excel**: تصدير الجداول والتقارير
- **استيراد Excel**: إضافة عملاء وموردين من ملفات Excel

## ⚙️ الإعدادات

7 تبويبات للإعدادات:

1. بيانات الشركة
2. قواعد الرصيد السالب
3. تنسيق الجداول والداشبورد
4. النسخ الاحتياطي التلقائي
5. الطباعة والتصدير
6. إدارة قاعدة البيانات
7. الثيمات

## 📊 الإحصائيات

| المؤشر | القيمة |
|--------|--------|
| ملفات Python | 67+ |
| جداول قاعدة البيانات | 21 |
| تبويبات الواجهات | 35+ |
| مكونات واجهة موحدة | 8 |
| سمات | 13 |

## 🔧 المكتبات المستخدمة

| المكتبة | الاستخدام |
|---------|-----------|
| PyQt6>=6.6.0 | واجهة المستخدم |
| SQLAlchemy>=2.0.0 | قاعدة البيانات (ORM) |
| python-dateutil>=2.8.2 | التواريخ |
| openpyxl>=3.1.0 | تصدير/استيراد Excel |
| reportlab>=4.0.0 | تصدير PDF |

## 📝 الترخيص

هذا المشروع مرخص بموجب [MIT License](LICENSE)

## 👨‍💻 المطوّر

**boukeroufa amine**  
📧 boukhroufa.tech@gmail.com  
🌐 https://github.com/boukhroufatech-rgb

## 📞 الدعم

للأسئلة أو المشاكل، يرجى فتح [Issue](https://github.com/boukhroufatech-rgb/shipping_company/issues) جديد.

---

> **آخر تحديث:** أبريل 2026 | **الإصدار:** 2.0
