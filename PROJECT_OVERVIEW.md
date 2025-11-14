# 📊 نظرة شاملة على المشروع FastAPI

## 🏗️ البنية الحالية

### **يوجد تطبيق FastAPI واحد فقط** في `main.py`

```
/opt/webhook_server/
├── main.py                    ⭐ التطبيق الرئيسي الوحيد
├── webhook_server.py          ❌ قديم (معطّل بالكامل - كود معلق)
└── ...
```

---

## 📦 التطبيق الرئيسي: `main.py`

### **معلومات التطبيق:**
```python
title: "Odoo Webhook & Medical API"
version: "3.0.0"
description: "API for Odoo webhooks, HPO Medical Terms, and Disease Diagnosis"
```

### **الـ Routers المسجلة (5 routers):**

```python
1. updates_router       من webhook/update_webhook.py
   └── /api/v1/check-updates
   └── /api/v1/cleanup

2. webhook_router       من webhook/webhook.py
   └── /api/v1/webhook/events

3. hpo_router          من hpo/hpo_routes.py
   └── /api/v1/hpo/*

4. disease_router      من hpo/disease_routes.py
   └── /api/v1/diseases/*

5. diagnosis_router    من hpo/diagnosis/enhanced_diagnosis_api.py
   └── /api/v1/diagnosis/*
```

---

## 🗂️ الوحدات (Modules)

### 1️⃣ **Webhook Module** (`/webhook/`)
```
webhook/
├── __init__.py
├── update_webhook.py      → Updates & Cleanup endpoints
└── webhook.py             → Webhook events handling
```

**الوظيفة:** إدارة Webhooks من Odoo

---

### 2️⃣ **HPO Module** (`/hpo/`)
```
hpo/
├── __init__.py
├── database.py            → اتصال PostgreSQL (Neon)
├── hpo_routes.py          → HPO Terms API
├── disease_routes.py      → Diseases & Diagnosis API
├── import_hpo.py          → سكريبت استيراد البيانات
├── link_specialties.py    → ربط التخصصات
└── diagnosis/             → التشخيص المحسّن ⭐
    ├── __init__.py
    ├── enhanced_diagnosis_api.py   → API endpoints
    ├── red_flags.py               → كشف الحالات الحرجة
    ├── cross_specialty.py         → تحليل متعدد التخصصات
    ├── differential_diagnosis.py  → التشخيص التفاضلي
    └── TEST_RESULTS.md           → تقرير الاختبارات
```

**الوظائف:**
- إدارة HPO Terms (Human Phenotype Ontology)
- تشخيص الأمراض
- كشف العلامات الحمراء الخطيرة
- تحليل متعدد التخصصات

---

### 3️⃣ **Core Module** (`/core/`)
```
core/
└── auth.py               → المصادقة (حالياً بسيط)
```

---

### 4️⃣ **Clients Module** (`/clients/`)
```
clients/
└── (ملفات العملاء - إن وجدت)
```

---

## 🎯 الخدمات المتاحة

### ✅ **الخدمات النشطة:**

| الخدمة | الحالة | المسارات |
|--------|--------|----------|
| **Webhook** | ✅ Active | `/api/v1/webhook/*` |
| **HPO Terms** | ✅ Active | `/api/v1/hpo/*` |
| **Diseases** | ✅ Active | `/api/v1/diseases/*` |
| **Enhanced Diagnosis** | ✅ Active | `/api/v1/diagnosis/*` |
| **Updates** | ✅ Active | `/api/v1/check-updates`, `/api/v1/cleanup` |

---

## 🗄️ قاعدة البيانات

### **PostgreSQL (Neon)**
```python
DATABASE_URL = "postgresql://neondb_owner:...@ep-holy-bonus-ag0vglfv-pooler.c-2.eu-central-1.aws.neon.tech/neondb"
```

**الجداول:**
- `hpo_terms` - المصطلحات الطبية
- `diseases` - الأمراض
- `disease_phenotypes` - علاقة الأمراض بالأعراض

---

## 🔧 الإعدادات

### **CORS:**
```python
ALLOWED_ORIGINS = [
    "https://app.propanel.ma",
    "https://flutter.propanel.ma",
    "http://localhost:3000",
    "http://localhost:5173"
]
```

### **Rate Limiting:**
- تحديد معدل الطلبات (slowapi)
- حد 429 عند التجاوز

---

## 📝 الملفات الإضافية

```
/opt/webhook_server/
├── config.py              → إعدادات المشروع
├── requirements.txt       → المكتبات المطلوبة
├── test_diagnosis_api.py  → اختبارات التشخيص
├── webhook.log           → سجلات Webhook
├── auth.log              → سجلات المصادقة
└── venv/                 → البيئة الافتراضية
```

---

## 🚫 الملفات القديمة/المعطلة

### ❌ `webhook_server.py`
- **الحالة:** معطّل بالكامل (كل الكود معلق)
- **السبب:** تم نقل كل الوظائف إلى `main.py` مع تحسينات
- **الإجراء المقترح:** يمكن حذفه بأمان

---

## 📊 إحصائيات المشروع

| العنصر | العدد |
|--------|-------|
| **تطبيقات FastAPI** | 1 (main.py) |
| **Routers** | 5 routers |
| **Modules** | 4 modules (webhook, hpo, core, clients) |
| **API Endpoints** | ~30+ endpoint |
| **قواعد البيانات** | 1 (PostgreSQL - Neon) |

---

## 🎯 الخلاصة

### ✅ **ما هو نشط:**
- ✅ تطبيق FastAPI واحد في `main.py`
- ✅ 5 routers متكاملة
- ✅ نظام تشخيص طبي محسّن
- ✅ اتصال بقاعدة بيانات PostgreSQL
- ✅ CORS و Rate Limiting

### ❌ **ما هو غير مستخدم:**
- ❌ `webhook_server.py` (قديم ومعطل)

### 🔧 **التوصيات:**
1. حذف `webhook_server.py` لتنظيف المشروع
2. الاحتفاظ بـ `main.py` كتطبيق رئيسي وحيد
3. جميع الوظائف تعمل بشكل ممتاز

---

## 🚀 كيفية التشغيل

```bash
# تشغيل السيرفر
cd /opt/webhook_server
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# الوصول للتوثيق
http://localhost:8000/docs        # Swagger UI
http://localhost:8000/redoc       # ReDoc
```

---

## 📌 النتيجة النهائية

**يوجد مشروع FastAPI واحد فقط:**
- `main.py` → التطبيق الرئيسي الوحيد النشط ✅
- `webhook_server.py` → قديم ومعطل (يمكن حذفه) ❌

**الحالة:** المشروع منظم وجاهز للإنتاج 🎉

