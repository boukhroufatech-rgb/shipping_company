# Shipping Company — الهيكل الكامل للبرنامج
# ================================================
# تاريخ الإنشاء: 2026-04-02
# الإصدار: 2.0
# ================================================

## 1. البنية العامة

```
shipping_company/
├── main.py                          # نقطة الدخول الرئيسية
├── requirements.txt                 # المكتبات المطلوبة
├── shipping_app.db                  # قاعدة البيانات SQLite
├── GOLDEN_RULES.md                  # القواعد الذهبية
├── UI_ARCHITECTURE.md               # توثيق الواجهات
├── ERRORS_LOG.md                    # سجل الأخطاء
├── PROJECT_STRUCTURE.md             # هذا الملف
│
├── core/                            # النواة
│   ├── database.py                  # إدارة قاعدة البيانات (SQLAlchemy)
│   ├── models.py                    # 20+ نموذج (Tables)
│   ├── repositories.py              # طبقة الوصول للبيانات
│   ├── services.py                  # خدمات النواة
│   ├── init_data.py                 # البيانات الأولية
│   └── themes.py                    # 13 ثيم (emerald, midnight, light...)
│
├── modules/                         # الوحدات (7)
│   ├── treasury/                    # الخزينة (DA)
│   │   ├── __init__.py
│   │   ├── views.py                 # 3 تبويبات: Comptes, Transferts, Journal
│   │   ├── service.py               # خدمات الخزينة
│   │   └── repository.py            # مستودع الخزينة
│   │
│   ├── currency/                    # العملات
│   │   ├── __init__.py
│   │   ├── views.py                 # 4 تبويبات: Soldes, Achats, Fournisseurs, Paiements
│   │   ├── service.py               # خدمات العملات
│   │   ├── repository.py            # مستودع العملات
│   │   └── world_dialog.py          # مكتبة العملات العالمية
│   │
│   ├── customers/                   # العملاء
│   │   ├── __init__.py
│   │   ├── views.py                 # 5 تبويبات: Clients, Marchandises, Paiements, Frais, Relevé
│   │   ├── service.py               # خدمات العملاء
│   │   └── repository.py            # مستودع العملاء
│   │
│   ├── licenses/                    # التراخيص
│   │   ├── __init__.py
│   │   ├── views.py                 # 4 تبويبات: Titulaires, Licences, Comptes, Transferts
│   │   ├── service.py               # (مشترك مع logistics)
│   │   └── repository.py            # (مشترك مع logistics)
│   │
│   ├── logistics/                   # اللوجستيك
│   │   ├── __init__.py
│   │   ├── views.py                 # 4 تبويبات: Agents, Paiements, Factures, Dépenses
│   │   ├── service.py               # خدمات اللوجستيك + التراخيص
│   │   ├── expense_service.py       # خدمات المصاريف
│   │   ├── repository.py            # مستودع اللوجستيك
│   │   ├── shipment_wizard.py       # معالج 3 خطوات (Facture)
│   │   └── OpenBillDialog            # (موجود لكن قديم)
│   │
│   ├── external_debt/               # الديون الخارجية
│   │   ├── __init__.py
│   │   ├── views.py
│   │   ├── service.py
│   │   └── repository.py
│   │
│   ├── partners/                    # الشركاء
│   │   ├── __init__.py
│   │   ├── views.py
│   │   ├── service.py
│   │   └── repository.py
│   │
│   ├── settings/                    # الإعدادات
│   │   ├── __init__.py
│   │   ├── views.py                 # 7 تبويبات
│   │   └── service.py               # خدمات الإعدادات + النسخ الاحتياطي
│   │
│   └── documents/                   # المستندات (جديد)
│       ├── __init__.py
│       └── generator.py             # مولّد المستندات (HTML → PDF)
│
├── components/                      # مكونات واجهة موحدة
│   ├── enhanced_table.py            # الجدول الموحد (نظام الشجرة)
│   ├── smart_form.py                # النموذج الذكي الموحد
│   ├── amount_input.py              # إدخال المبالغ
│   ├── dialogs.py                   # حوارات مساعدة
│   ├── error_dialog.py              # حوارات الأخطاء
│   ├── catalog_dialog.py            # كتالوج الأنواع
│   ├── status_filter.py             # فلتر الحالة
│   ├── summary_card.py              # بطاقات الملخص
│   └── loading_widget               # مؤشر التحميل
│
├── utils/                           # الأدوات المساعدة
│   ├── constants.py                 # الثوابت والقوالب
│   ├── formatters.py                # المنسقات (أرقام، تواريخ)
│   ├── validators.py                # المحققون
│   ├── logger.py                    # نظام السجلات
│   ├── error_handler.py             # معالج الأخطاء
│   └── icon_manager.py              # إدارة الأيقونات
│
├── assets/                          # الموارد
│   └── icons/                       # الأيقونات SVG
│       ├── plus.svg, file-text.svg, file-spreadsheet.svg
│       ├── printer.svg, circle-dollar-sign.svg
│       └── ... (40+ أيقونة)
│
└── backups/                         # النسخ الاحتياطية
```

## 2. قاعدة البيانات — النماذج

```
Tables:
├── currencies                        العملات (DA, USD, EUR, CNY, AED)
├── exchange_rates                    أسعار الصرف
├── accounts                          الحسابات (CAISSE, BANQUE, CCP, COMPTE)
├── transactions                      المعاملات المالية (CREDIT/DEBIT)
├── currency_suppliers                الموردين (CURRENCY, LICENSE, SHIPPING)
├── currency_purchases                عمليات شراء العملات
├── supplier_payments                 تسديدات الموردين
├── import_licenses                   التراخيص
├── container_files                   ملفات الحاويات (الفواتير)
├── container_expenses                مصاريف الحاويات
├── customer_goods                    بضائع العملاء
├── customer_payments                 تسديدات العملاء
├── customer_side_costs               مصاريف جانبية للعملاء
├── customers                         العملاء
├── partners                          الشركاء
├── partner_transactions              معاملات الشركاء
├── external_contacts                 جهات الديون الخارجية
├── external_transactions             معاملات الديون الخارجية
├── settings                          الإعدادات
├── treasury_account_types            أنواع حسابات الخزينة
├── license_goods                     أنواع بضائع التراخيص
└── expense_types                     أنواع المصاريف
```

## 3. نظام التبويبات — الشجرة

```
MainApp (التطبيق الرئيسي)
│
├── DashboardView (لوحة التحكم)
│   └── Summary cards + Charts
│
├── TreasuryView (الخزينة)
│   ├── Comptes          (الحسابات)
│   ├── Transferts       (التحويلات)
│   └── Journal          (سجل المعاملات)
│
├── CurrencyView (العملات)
│   ├── Soldes           (الأرصدة)
│   ├── Achats           (الشراء)
│   ├── Fournisseurs     (العملة)
│   └── Paiements        (التسديدات)
│
├── ClientsView (العملاء)
│   ├── Clients          (قائمة العملاء)
│   ├── Marchandises     (البضائع)
│   ├── Paiements        (التسديدات)
│   ├── Frais Annexes    (مصاريف جانبية)
│   └── Relevé           (كشف الحساب)
│
├── LicensesView (التراخيص)
│   ├── Titulaires       (أصحاب الرخصة)
│   ├── Licences          (الرخص)
│   ├── Comptes Bancaires (الحسابات البنكية)
│   └── Transferts       (تحويلات DA)
│
├── LogisticsView (اللوجستيك)
│   ├── Agents           (وكلاء الشحن)
│   ├── Paiements        (تسديدات الوكلاء)
│   ├── Factures         (الفواتير/الحاويات)
│   └── Dépenses         (المصاريف)
│
├── ExternalDebtView (الديون الخارجية)
│
├── PartnersView (الشركاء)
│
└── SettingsView (الإعدادات)
    ├── Institution      (بيانات الشركة)
    ├── Règles de Gestion (قواعد الرصيد السالب)
    ├── Interface        (تنسيق الجداول والداشبورد)
    ├── Sauvegarde Auto  (النسخ التلقائي)
    ├── Impression & Export (الطباعة والتصدير)
    ├── Base de Données  (إدارة قاعدة البيانات)
    └── Theme            (الثيمات)
```

## 4. نظام المكونات الموحدة (الشجرة)

```
EnhancedTableView (الجدول الموحد)
├── Toolbar: [+Nouveau] [Modifier] [Supprimer] [Restaurer] [Rafraîchir]
│           [📄PDF] [📊Excel] [🖨️Imprimer] [Colonnes]
├── Search: [🔍 Rechercher...]
├── Table: الجدول الرئيسي
├── Footer: ملخص (Nombre, Total...)
└── StatusFilter: [Active ▼]

SmartFormDialog (النموذج الموحد)
├── Dynamic fields: text, dropdown, number, date, multiline
├── Quick Add [+] بجانب كل dropdown
└── Validation automatique

퀵 Add Pattern (الاختصار):
  Dropdown [v] [+] → فتح نافذة إضافة → تحديث القائمة → اختيار الجديد
```

## 5. التسميات الموحدة

| المفهوم | التبويب | الحقل | الدالة |
|---------|---------|-------|--------|
| مالك الرخصة | Titulaires | Titulaire | on_add_owner |
| وكيل الشحن | Agents | Agent | quick_add_agent |
| عميل | Clients | Client | customer_service |
| حاوية | Conteneurs | Conteneur | container_service |
| بضاعة | Marchandises | Marchandise | goods_service |
| شحنة/فاتورة | Factures | Facture | shipment_service |
| تحويل | Transferts | Transfert | transfer_service |
| مورد عملة | Fournisseurs | Fournisseur | supplier_service |
| مصروف | Dépenses | Dépense | expense_service |

## 6. ألوان الجداول الموحدة

| اللون | الرمز | المعنى |
|-------|-------|--------|
| أخضر | #072b25 | موجب / متاح / دائن |
| أحمر | #2b0707 | سالب / مستنفذ / مدين |
| رمادي | #1a1a1a | مؤرشف / غير نشط |
| أزرق | #2c3e50 | العملة الافتراضية (DA) |
| ذهبي | #4d3d00 | في الانتظار (pending) |

## 7. المكتبات المطلوبة

```
PyQt6>=6.6.0              # واجهة المستخدم
SQLAlchemy>=2.0.0          # قاعدة البيانات
python-dateutil>=2.8.2     # التواريخ
openpyxl>=3.1.0            # تصدير/استيراد Excel
reportlab>=4.0.0           # تصدير PDF
```

## 8. ملفات المشروع

| الملف | الوصف |
|-------|-------|
| main.py | نقطة الدخول + refresh_all + closeEvent |
| core/database.py | get_session, create_all |
| core/models.py | كل النماذج (20+ جدول) |
| core/repositories.py | BaseRepository (CRUD) |
| core/init_data.py | البيانات الأولية (عملات + حسابات) |
| core/themes.py | 13 ثيم |
| components/enhanced_table.py | الجدول الموحد |
| components/smart_form.py | النموذج الموحد |
| components/dialogs.py | حوارات مساعدة |
| utils/constants.py | الثوابت والقوالب |
| utils/formatters.py | format_amount, format_date |
| utils/logger.py | نظام التسجيل |
| ERRORS_LOG.md | سجل الأخطاء المستفادة |
| PROJECT_STRUCTURE.md | هذا الملف |

## 9. القواعد الذهبية

1. **نظام الشجرة**: الجذر = EnhancedTableView (تعديل واحد يؤثر على الكل)
2. **توثيق [CUSTOM]**: أي تعديل مخصص يحتاج [WHY] + [DATE]
3. **لا يدوي**: كل شيء آلي ومركزي
4. **الفرنسية**: التعليقات والواجهة بالفرنسية
5. **Quick Add [+]**: كل dropdown يحتاج إضافة → [+] يفتح نافذة
6. **التسمية الموحدة**: نفس المفهوم = نفس الاسم في كل مكان
7. **الألوان الموحدة**: نفس الحالة = نفس اللون في كل الجداول
8. **المستندات**: Facture / Reçu / Relevé عبر DocumentGenerator

## 10. الميزات الرئيسية

| الميزة | الوصف | الحالة |
|--------|-------|--------|
| الخزينة DA | حسابات + تحويلات + سجل | ✅ |
| العملات | شراء + موردين + تسديد | ✅ |
| العملاء | قائمة + بضائع + تسديد + كشف | ✅ |
| التراخيص | مالكين + رخص + حسابات + تحويل | ✅ |
| اللوجستيك | وكلاء + فواتير + حاويات + مصاريف | ✅ |
| الديون الخارجية | جهات + معاملات + أرصدة | ✅ |
| الشركاء | قائمة + حسابات + معاملات | ✅ |
| الإعدادات | 7 تبويبات + ثيمات | ✅ |
| تصدير Excel | جداول + فواتير + تقارير | ✅ |
| تصدير PDF | فواتير + إيصالات + كشوف | ✅ |
| استيراد Excel | عملاء + موردين | ✅ |
| معاينة الطباعة | QPrintPreviewDialog | ✅ |
| القواعد الذهبية | 11 قاعدة موثقة | ✅ |

---
**آخر تحديث:** 2026-04-02 17:00
**عدد الملفات:** 67 Python files
**عدد النماذج:** 21 tables
**عدد التبويبات:** 35 tabs
**عدد المكونات الموحدة:** 8 components
