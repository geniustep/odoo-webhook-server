# 🚀 Odoo Webhook Server

<div dir="rtl">

## 📋 نظرة عامة

نظام متكامل لإدارة Webhooks من Odoo مبني على FastAPI، يوفر واجهات برمجية قوية وآمنة للتكامل مع نظام Odoo ERP.

</div>

## ✨ Features | المميزات

- 🔄 **Webhook Event Handling** - معالجة أحداث Webhook من Odoo في الوقت الفعلي
- 🔍 **Updates Tracking** - تتبع ومراقبة التحديثات
- 🧹 **Auto Cleanup** - تنظيف تلقائي للبيانات القديمة
- 🔒 **Authentication** - نظام مصادقة آمن
- ⚡ **Rate Limiting** - حماية من الطلبات الزائدة
- 🌐 **CORS Support** - دعم كامل للطلبات عبر النطاقات
- 🐳 **Docker Ready** - جاهز للتشغيل عبر Docker
- 📊 **API Documentation** - توثيق تفاعلي للـ API (Swagger/ReDoc)

---

## 🏗️ Project Structure | البنية

```
/opt/webhook_server/
├── main.py                    # التطبيق الرئيسي FastAPI
├── config.py                  # إعدادات المشروع
├── requirements.txt           # المتطلبات
├── Dockerfile                 # ملف Docker
├── .dockerignore             # استثناءات Docker
│
├── webhook/                   # وحدة Webhook
│   ├── __init__.py
│   ├── webhook.py            # معالجة أحداث Webhook
│   └── update_webhook.py     # تتبع التحديثات
│
├── core/                      # الوحدة الأساسية
│   └── auth.py               # نظام المصادقة
│
└── clients/                   # عملاء API
    └── odoo_client.py        # عميل Odoo
```

---

## 📋 Requirements | المتطلبات

### System Requirements | متطلبات النظام

- Python 3.12+
- pip (مدير الحزم Python)
- Docker (اختياري)

### Python Dependencies | مكتبات Python

```
fastapi - إطار العمل الرئيسي
uvicorn - خادم ASGI
httpx - عميل HTTP
slowapi - تحديد معدل الطلبات
python-dotenv - إدارة متغيرات البيئة
```

---

## 🚀 Installation | التثبيت

### 1️⃣ Clone Repository | استنساخ المستودع

```bash
git clone https://github.com/geniustep/FastAPI.git
cd FastAPI
```

### 2️⃣ Create Virtual Environment | إنشاء البيئة الافتراضية

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# أو
venv\Scripts\activate  # On Windows
```

### 3️⃣ Install Dependencies | تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment | إعداد البيئة

أنشئ ملف `.env` في الجذر:

```env
# Odoo Configuration
ODOO_URL=https://app.propanel.ma
ODOO_DB=your_database
ODOO_USERNAME=admin
ODOO_PASSWORD=your_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 🎯 Running the Application | تشغيل التطبيق

### Development Mode | وضع التطوير

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode | وضع الإنتاج

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker | استخدام Docker

```bash
# Build image | بناء الصورة
docker build -t odoo-webhook-server .

# Run container | تشغيل الحاوية
docker run -d \
  --name odoo-webhook-server \
  -p 8000:8000 \
  --env-file .env \
  odoo-webhook-server
```

### Docker Compose (Recommended) | استخدام Docker Compose

أنشئ ملف `docker-compose.yml`:

```yaml
version: '3.8'

services:
  webhook-server:
    build: .
    container_name: odoo-webhook-server
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./webhook.log:/app/webhook.log
      - ./auth.log:/app/auth.log
```

ثم شغّل:

```bash
docker-compose up -d
```

---

## 📚 API Documentation | توثيق API

بعد تشغيل التطبيق، يمكنك الوصول للتوثيق التفاعلي:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints | نقاط النهاية الرئيسية

#### 🏠 Health Check

```http
GET /
```

**Response:**
```json
{
  "message": "Welcome to Odoo Webhook Server",
  "status": "running",
  "version": "2.0.0",
  "services": {
    "webhook": "active",
    "check_updates": "active",
    "cleanup": "active"
  }
}
```

#### 🔔 Webhook Events

```http
POST /api/v1/webhook/events
Content-Type: application/json

{
  "event": "create",
  "model": "res.partner",
  "record_id": 123,
  "data": {...}
}
```

#### 🔍 Check Updates

```http
GET /api/v1/check-updates?model=res.partner&last_update=2024-01-01
```

#### 🧹 Cleanup

```http
DELETE /api/v1/cleanup?days=30
```

---

## 🔒 Security | الأمان

### CORS Configuration | إعداد CORS

النطاقات المسموحة مُعرّفة في `main.py`:

```python
ALLOWED_ORIGINS = [
    "https://app.propanel.ma",
    "https://flutter.propanel.ma",
    "http://localhost:3000",
    "http://localhost:5173",
]
```

### Rate Limiting | تحديد معدل الطلبات

- تُطبق حدود على جميع نقاط النهاية
- يمنع هجمات DDoS والطلبات المفرطة
- يُرجع `429 Too Many Requests` عند التجاوز

### Authentication | المصادقة

```python
# في core/auth.py
# يمكن تخصيص نظام المصادقة حسب الحاجة
```

---

## 📊 Logging | السجلات

يتم حفظ السجلات في الملفات التالية:

- `webhook.log` - سجلات أحداث Webhook
- `auth.log` - سجلات المصادقة

### Log Format | تنسيق السجل

```
[2024-11-14 10:30:00] INFO - Webhook received: create res.partner #123
[2024-11-14 10:30:01] INFO - Processing completed successfully
```

---

## 🔧 Configuration | الإعدادات

### config.py

```python
import os
from dotenv import load_dotenv

load_dotenv()

ODOO_URL = os.getenv("ODOO_URL", "https://app.propanel.ma")
```

### Environment Variables | متغيرات البيئة

| Variable | Description | Default |
|----------|-------------|---------|
| `ODOO_URL` | رابط خادم Odoo | https://app.propanel.ma |
| `ODOO_DB` | قاعدة بيانات Odoo | - |
| `ODOO_USERNAME` | اسم المستخدم | - |
| `ODOO_PASSWORD` | كلمة المرور | - |
| `API_HOST` | عنوان IP للخادم | 0.0.0.0 |
| `API_PORT` | المنفذ | 8000 |

---

## 🧪 Testing | الاختبار

```bash
# تشغيل الاختبارات
pytest

# مع التغطية
pytest --cov=.

# اختبار نقطة نهاية معينة
curl -X GET http://localhost:8000/
```

### Manual Testing | اختبار يدوي

```bash
# اختبار Health Check
curl http://localhost:8000/

# اختبار Webhook
curl -X POST http://localhost:8000/api/v1/webhook/events \
  -H "Content-Type: application/json" \
  -d '{"event":"create","model":"res.partner","record_id":123}'
```

---

## 🔄 API Versioning | إصدارات API

النظام يدعم إصدارات API عبر المسارات:

```
/api/v1/...  - الإصدار الحالي
/api/v2/...  - إصدارات مستقبلية
```

---

## 📈 Monitoring | المراقبة

### Health Check Endpoint

```bash
curl http://localhost:8000/
```

### Docker Health Check

```bash
docker inspect --format='{{.State.Health.Status}}' odoo-webhook-server
```

### Logs Monitoring

```bash
# متابعة السجلات المباشرة
tail -f webhook.log

# في Docker
docker logs -f odoo-webhook-server
```

---

## 🐛 Troubleshooting | حل المشاكل

### المشكلة: الخادم لا يعمل

<div dir="rtl">

**الحل:**
1. تحقق من أن المنفذ 8000 غير مستخدم
2. تأكد من تثبيت جميع المتطلبات
3. راجع ملف السجلات

</div>

```bash
# تحقق من المنفذ
lsof -i :8000

# أعد تثبيت المتطلبات
pip install -r requirements.txt --force-reinstall
```

### المشكلة: CORS Errors

<div dir="rtl">

**الحل:** أضف النطاق الخاص بك في `main.py`

</div>

```python
ALLOWED_ORIGINS = [
    # ... الموجود
    "https://your-domain.com",
]
```

### المشكلة: Rate Limit Exceeded

<div dir="rtl">

**الحل:** انتظر قليلاً أو قم بتعديل حدود المعدل

</div>

---

## 🤝 Contributing | المساهمة

<div dir="rtl">

نرحب بمساهماتكم! الرجاء اتباع الخطوات التالية:

</div>

1. Fork المشروع
2. أنشئ فرعًا للميزة (`git checkout -b feature/AmazingFeature`)
3. Commit التغييرات (`git commit -m 'Add AmazingFeature'`)
4. Push للفرع (`git push origin feature/AmazingFeature`)
5. افتح Pull Request

### Code Style | أسلوب الكود

```bash
# استخدم Black للتنسيق
black .

# استخدم flake8 للتحقق
flake8 .
```

---

## 📝 Changelog | سجل التغييرات

### Version 2.0.0 (Current)

- ✨ إعادة هيكلة المشروع بالكامل
- 🐳 إضافة دعم Docker
- 🔒 تحسينات الأمان
- ⚡ تحسين الأداء
- 📚 توثيق شامل

### Version 1.0.0

- 🎉 الإصدار الأولي

---

## 📜 License | الترخيص

<div dir="rtl">

هذا المشروع مرخص تحت رخصة MIT - راجع ملف LICENSE للتفاصيل.

</div>

---

## 👥 Authors & Contributors | المؤلفون والمساهمون

- **GeniusStep Team** - [GitHub](https://github.com/geniustep)

---

## 🔗 Related Projects | مشاريع ذات صلة

- [Odoo](https://www.odoo.com/) - نظام ERP
- [FastAPI](https://fastapi.tiangolo.com/) - إطار العمل
- [ProPanel](https://app.propanel.ma) - لوحة التحكم

---

## 📞 Support | الدعم

<div dir="rtl">

للدعم والاستفسارات:

- 📧 Email: support@propanel.ma
- 🌐 Website: https://propanel.ma
- 📝 Issues: [GitHub Issues](https://github.com/geniustep/FastAPI/issues)

</div>

---

## ⭐ Show Your Support

<div dir="rtl">

إذا أعجبك هذا المشروع، أعطه نجمة ⭐️ على GitHub!

</div>

---

<div align="center">

**Made with ❤️ by GeniusStep Team**

</div>

