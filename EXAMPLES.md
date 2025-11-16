# 📚 أمثلة عملية - Smart Sync API v2.0

## 🎯 السيناريوهات الواقعية

---

## 1️⃣ تطبيق المبيعات (Sales App)

### Flutter/Dart

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:device_info_plus/device_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SyncService {
  final String baseUrl = 'https://webhook-server.propanel.ma';
  final String sessionId;
  final int userId;

  SyncService({required this.sessionId, required this.userId});

  Future<String> getDeviceId() async {
    final deviceInfo = DeviceInfoPlugin();
    if (Platform.isAndroid) {
      final androidInfo = await deviceInfo.androidInfo;
      return 'android-${androidInfo.id}';
    } else {
      final iosInfo = await deviceInfo.iosInfo;
      return 'ios-${iosInfo.identifierForVendor}';
    }
  }

  Future<SyncResult> syncData() async {
    try {
      final deviceId = await getDeviceId();

      final response = await http.post(
        Uri.parse('$baseUrl/api/v2/sync/pull'),
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Id': sessionId,
        },
        body: jsonEncode({
          'user_id': userId,
          'device_id': deviceId,
          'app_type': 'sales_app',
          'limit': 100,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        if (data['has_updates']) {
          print('📥 Found ${data['new_events_count']} new events');

          // معالجة الأحداث
          for (var event in data['events']) {
            await processEvent(event);
          }

          // حفظ token للمرة القادمة
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('sync_token', data['next_sync_token']);

          return SyncResult(
            success: true,
            eventsCount: data['new_events_count'],
          );
        } else {
          print('✅ No new updates');
          return SyncResult(success: true, eventsCount: 0);
        }
      } else {
        throw Exception('Sync failed: ${response.statusCode}');
      }
    } catch (e) {
      print('❌ Sync error: $e');
      return SyncResult(success: false, error: e.toString());
    }
  }

  Future<void> processEvent(Map<String, dynamic> event) async {
    final model = event['model'];
    final recordId = event['record_id'];
    final eventType = event['event'];

    print('Processing: $eventType on $model #$recordId');

    switch (model) {
      case 'sale.order':
        if (eventType == 'create') {
          await fetchAndStoreOrder(recordId);
        } else if (eventType == 'write') {
          await updateOrder(recordId);
        } else if (eventType == 'unlink') {
          await deleteOrder(recordId);
        }
        break;

      case 'res.partner':
        if (eventType == 'create') {
          await fetchAndStoreCustomer(recordId);
        } else if (eventType == 'write') {
          await updateCustomer(recordId);
        }
        break;

      case 'product.template':
        if (eventType == 'create' || eventType == 'write') {
          await fetchAndStoreProduct(recordId);
        }
        break;
    }
  }

  Future<void> fetchAndStoreOrder(int orderId) async {
    // جلب الطلب من Odoo وحفظه محلياً
    print('Fetching order #$orderId from Odoo...');
    // ... implementation
  }

  Future<void> updateOrder(int orderId) async {
    print('Updating order #$orderId...');
    // ... implementation
  }

  Future<void> deleteOrder(int orderId) async {
    print('Deleting order #$orderId...');
    // ... implementation
  }

  Future<void> fetchAndStoreCustomer(int customerId) async {
    print('Fetching customer #$customerId...');
    // ... implementation
  }

  Future<void> updateCustomer(int customerId) async {
    print('Updating customer #$customerId...');
    // ... implementation
  }

  Future<void> fetchAndStoreProduct(int productId) async {
    print('Fetching product #$productId...');
    // ... implementation
  }
}

class SyncResult {
  final bool success;
  final int eventsCount;
  final String? error;

  SyncResult({required this.success, this.eventsCount = 0, this.error});
}

// الاستخدام في التطبيق
void main() async {
  final syncService = SyncService(
    sessionId: 'your_session_id',
    userId: 5,
  );

  // مزامنة كل 30 ثانية
  Timer.periodic(Duration(seconds: 30), (_) async {
    await syncService.syncData();
  });
}
```

---

## 2️⃣ تطبيق التوصيل (Delivery App)

### React Native / TypeScript

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';
import DeviceInfo from 'react-native-device-info';

interface SyncRequest {
  user_id: number;
  device_id: string;
  app_type: string;
  limit: number;
}

interface SyncResponse {
  status: string;
  has_updates: boolean;
  new_events_count: number;
  events: Event[];
  next_sync_token: string;
}

interface Event {
  id: number;
  model: string;
  record_id: number;
  event: 'create' | 'write' | 'unlink';
  timestamp: string;
}

class DeliverySync {
  private baseUrl = 'https://webhook-server.propanel.ma';
  private sessionId: string;
  private userId: number;

  constructor(sessionId: string, userId: number) {
    this.sessionId = sessionId;
    this.userId = userId;
  }

  async syncDeliveries(): Promise<void> {
    try {
      const deviceId = await DeviceInfo.getUniqueId();

      const request: SyncRequest = {
        user_id: this.userId,
        device_id: `rn-${deviceId}`,
        app_type: 'delivery_app',
        limit: 50,
      };

      const response = await fetch(`${this.baseUrl}/api/v2/sync/pull`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Id': this.sessionId,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Sync failed: ${response.status}`);
      }

      const data: SyncResponse = await response.json();

      if (data.has_updates) {
        console.log(`📦 New deliveries: ${data.new_events_count}`);

        // فلتر فقط stock.picking (الشحنات)
        const pickings = data.events.filter(e => e.model === 'stock.picking');

        for (const event of pickings) {
          await this.handlePickingEvent(event);
        }

        // حفظ token
        await AsyncStorage.setItem('delivery_sync_token', data.next_sync_token);

        // إشعار للموصل
        await this.showNotification(`${pickings.length} شحنات جديدة!`);
      }
    } catch (error) {
      console.error('Sync error:', error);
    }
  }

  async handlePickingEvent(event: Event): Promise<void> {
    switch (event.event) {
      case 'create':
        // شحنة جديدة
        await this.fetchPickingDetails(event.record_id);
        break;

      case 'write':
        // تحديث حالة الشحنة (ربما جاهزة للتوصيل)
        await this.updatePickingStatus(event.record_id);
        break;

      case 'unlink':
        // شحنة ملغاة
        await this.removePickingFromQueue(event.record_id);
        break;
    }
  }

  async fetchPickingDetails(pickingId: number): Promise<void> {
    // جلب تفاصيل الشحنة من Odoo
    console.log(`Fetching picking #${pickingId}...`);

    // مثال: استدعاء Odoo API
    const response = await fetch(
      `https://app.propanel.ma/api/stock/picking/${pickingId}`,
      {
        headers: { 'X-Session-Id': this.sessionId }
      }
    );

    const picking = await response.json();

    // حفظ محلياً
    await AsyncStorage.setItem(
      `picking_${pickingId}`,
      JSON.stringify(picking)
    );

    console.log(`✅ Saved picking #${pickingId}`);
  }

  async updatePickingStatus(pickingId: number): Promise<void> {
    console.log(`Updating picking #${pickingId}...`);
    // ... implementation
  }

  async removePickingFromQueue(pickingId: number): Promise<void> {
    console.log(`Removing picking #${pickingId}...`);
    await AsyncStorage.removeItem(`picking_${pickingId}`);
  }

  async showNotification(message: string): Promise<void> {
    // عرض إشعار push
    console.log(`📢 ${message}`);
    // ... implementation with react-native-push-notification
  }
}

// الاستخدام
const deliverySync = new DeliverySync('session_id', 42);

// مزامنة كل دقيقة
setInterval(() => {
  deliverySync.syncDeliveries();
}, 60000);
```

---

## 3️⃣ لوحة تحكم المدير (Manager Dashboard)

### React / JavaScript

```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ManagerDashboard = () => {
  const [updates, setUpdates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [syncStats, setSyncStats] = useState(null);

  const sessionId = localStorage.getItem('session_id');
  const userId = parseInt(localStorage.getItem('user_id'));

  useEffect(() => {
    // مزامنة كل 10 ثواني
    const interval = setInterval(syncUpdates, 10000);

    // مزامنة فورية
    syncUpdates();

    return () => clearInterval(interval);
  }, []);

  const syncUpdates = async () => {
    setLoading(true);

    try {
      const deviceId = getDeviceId();

      const response = await axios.post(
        'https://webhook-server.propanel.ma/api/v2/sync/pull',
        {
          user_id: userId,
          device_id: deviceId,
          app_type: 'manager_app',
          limit: 200,
        },
        {
          headers: {
            'X-Session-Id': sessionId,
          }
        }
      );

      const data = response.data;

      if (data.has_updates) {
        console.log(`📊 ${data.new_events_count} new events`);

        // تجميع حسب النموذج
        const summary = groupByModel(data.events);

        setUpdates(prevUpdates => [
          ...data.events,
          ...prevUpdates
        ].slice(0, 100)); // آخر 100 حدث

        // عرض إشعار
        showNotification(summary);
      }
    } catch (error) {
      console.error('Sync error:', error);
    } finally {
      setLoading(false);
    }
  };

  const groupByModel = (events) => {
    const summary = {};

    events.forEach(event => {
      const model = event.model;
      if (!summary[model]) {
        summary[model] = { create: 0, write: 0, unlink: 0 };
      }
      summary[model][event.event]++;
    });

    return summary;
  };

  const showNotification = (summary) => {
    const messages = Object.entries(summary).map(([model, counts]) => {
      const total = counts.create + counts.write + counts.unlink;
      return `${getModelName(model)}: ${total}`;
    });

    if (messages.length > 0) {
      new Notification('تحديثات جديدة', {
        body: messages.join('\n'),
        icon: '/logo.png'
      });
    }
  };

  const getModelName = (model) => {
    const names = {
      'sale.order': 'طلبات البيع',
      'res.partner': 'العملاء',
      'stock.picking': 'الشحنات',
      'account.move': 'الفواتير',
      'hr.expense': 'المصروفات',
    };
    return names[model] || model;
  };

  const getDeviceId = () => {
    let deviceId = localStorage.getItem('device_id');
    if (!deviceId) {
      deviceId = `web-${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('device_id', deviceId);
    }
    return deviceId;
  };

  const getSyncState = async () => {
    try {
      const deviceId = getDeviceId();
      const response = await axios.get(
        `https://webhook-server.propanel.ma/api/v2/sync/state`,
        {
          params: {
            user_id: userId,
            device_id: deviceId,
          },
          headers: {
            'X-Session-Id': sessionId,
          }
        }
      );

      setSyncStats(response.data);
    } catch (error) {
      console.error('Error fetching sync state:', error);
    }
  };

  return (
    <div className="dashboard">
      <h1>لوحة التحكم</h1>

      {loading && <div className="spinner">جاري المزامنة...</div>}

      <div className="sync-info">
        <button onClick={getSyncState}>عرض حالة المزامنة</button>

        {syncStats && (
          <div className="stats">
            <p>آخر مزامنة: {new Date(syncStats.last_sync_time).toLocaleString('ar')}</p>
            <p>عدد المزامنات: {syncStats.sync_count}</p>
            <p>آخر حدث: #{syncStats.last_event_id}</p>
          </div>
        )}
      </div>

      <div className="updates-list">
        <h2>التحديثات الأخيرة</h2>

        {updates.map(event => (
          <div key={event.id} className="update-item">
            <span className={`badge ${event.event}`}>{event.event}</span>
            <span className="model">{getModelName(event.model)}</span>
            <span className="record">#{event.record_id}</span>
            <span className="time">
              {new Date(event.timestamp).toLocaleTimeString('ar')}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ManagerDashboard;
```

---

## 4️⃣ خدمة المزامنة الخلفية (Background Sync Service)

### Python

```python
import time
import requests
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundSyncService:
    """خدمة مزامنة خلفية لمزامنة Odoo مع نظام خارجي"""

    def __init__(self, webhook_url, session_id, user_id, external_system_url):
        self.webhook_url = webhook_url
        self.session_id = session_id
        self.user_id = user_id
        self.external_system_url = external_system_url
        self.device_id = "sync-service-001"

    def run(self):
        """تشغيل الخدمة - حلقة لا نهائية"""
        logger.info("🚀 Starting background sync service...")

        while True:
            try:
                self.sync_cycle()
                time.sleep(60)  # كل دقيقة
            except KeyboardInterrupt:
                logger.info("🛑 Service stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Sync error: {e}")
                time.sleep(10)  # انتظر 10 ثواني قبل المحاولة مرة أخرى

    def sync_cycle(self):
        """دورة مزامنة واحدة"""
        logger.info("🔄 Starting sync cycle...")

        # 1. اجلب التحديثات من Odoo
        updates = self.fetch_updates()

        if not updates['has_updates']:
            logger.info("✅ No new updates")
            return

        logger.info(f"📥 Found {updates['new_events_count']} new events")

        # 2. معالجة كل حدث
        for event in updates['events']:
            try:
                self.process_event(event)
            except Exception as e:
                logger.error(f"❌ Error processing event {event['id']}: {e}")
                # سجل الخطأ ولكن استمر

        logger.info("✅ Sync cycle completed")

    def fetch_updates(self):
        """جلب التحديثات من Webhook Server"""
        response = requests.post(
            f"{self.webhook_url}/api/v2/sync/pull",
            headers={
                "Content-Type": "application/json",
                "X-Session-Id": self.session_id
            },
            json={
                "user_id": self.user_id,
                "device_id": self.device_id,
                "app_type": "manager_app",
                "limit": 100
            }
        )

        response.raise_for_status()
        return response.json()

    def process_event(self, event):
        """معالجة حدث واحد"""
        model = event['model']
        record_id = event['record_id']
        event_type = event['event']

        logger.info(f"Processing: {event_type} on {model} #{record_id}")

        # مزامنة حسب النموذج
        if model == 'res.partner':
            self.sync_customer(record_id, event_type)
        elif model == 'sale.order':
            self.sync_order(record_id, event_type)
        elif model == 'product.template':
            self.sync_product(record_id, event_type)

    def sync_customer(self, customer_id, event_type):
        """مزامنة عميل مع النظام الخارجي"""
        if event_type == 'unlink':
            # حذف من النظام الخارجي
            self.delete_from_external_system('customers', customer_id)
        else:
            # جلب من Odoo
            customer = self.fetch_from_odoo('res.partner', customer_id)

            # إرسال للنظام الخارجي
            self.upsert_to_external_system('customers', customer_id, customer)

    def sync_order(self, order_id, event_type):
        """مزامنة طلب"""
        if event_type == 'unlink':
            self.delete_from_external_system('orders', order_id)
        else:
            order = self.fetch_from_odoo('sale.order', order_id)
            self.upsert_to_external_system('orders', order_id, order)

    def sync_product(self, product_id, event_type):
        """مزامنة منتج"""
        if event_type == 'unlink':
            self.delete_from_external_system('products', product_id)
        else:
            product = self.fetch_from_odoo('product.template', product_id)
            self.upsert_to_external_system('products', product_id, product)

    def fetch_from_odoo(self, model, record_id):
        """جلب سجل من Odoo"""
        # استخدم Odoo JSON-RPC API
        # هذا مثال مبسط
        logger.info(f"Fetching {model} #{record_id} from Odoo")

        # TODO: تنفيذ فعلي
        return {
            'id': record_id,
            'model': model,
            # ... بيانات أخرى
        }

    def upsert_to_external_system(self, resource, record_id, data):
        """إرسال/تحديث في النظام الخارجي"""
        logger.info(f"Upserting {resource} #{record_id} to external system")

        try:
            response = requests.post(
                f"{self.external_system_url}/api/{resource}/{record_id}",
                json=data
            )
            response.raise_for_status()
            logger.info(f"✅ Synced {resource} #{record_id}")
        except Exception as e:
            logger.error(f"❌ Failed to sync {resource} #{record_id}: {e}")
            raise

    def delete_from_external_system(self, resource, record_id):
        """حذف من النظام الخارجي"""
        logger.info(f"Deleting {resource} #{record_id} from external system")

        try:
            response = requests.delete(
                f"{self.external_system_url}/api/{resource}/{record_id}"
            )
            response.raise_for_status()
            logger.info(f"✅ Deleted {resource} #{record_id}")
        except Exception as e:
            logger.error(f"❌ Failed to delete {resource} #{record_id}: {e}")

# الاستخدام
if __name__ == "__main__":
    service = BackgroundSyncService(
        webhook_url="https://webhook-server.propanel.ma",
        session_id="your_session_id_here",
        user_id=2,
        external_system_url="https://external-crm.example.com"
    )

    service.run()
```

---

## 🔍 نصائح وأفضل الممارسات

### 1. **معالجة الأخطاء**
```typescript
async function safeSync() {
  let retries = 0;
  const maxRetries = 3;

  while (retries < maxRetries) {
    try {
      await syncData();
      return;
    } catch (error) {
      retries++;
      if (retries >= maxRetries) {
        // أبلغ المستخدم
        showError('فشلت المزامنة بعد 3 محاولات');
      } else {
        // انتظر قبل المحاولة مرة أخرى
        await sleep(Math.pow(2, retries) * 1000);
      }
    }
  }
}
```

### 2. **Offline Support**
```dart
Future<void> syncWhenOnline() async {
  // تحقق من الاتصال
  var connectivityResult = await Connectivity().checkConnectivity();

  if (connectivityResult == ConnectivityResult.none) {
    print('⚠️ No internet connection, sync postponed');
    // حفظ للمزامنة لاحقاً
    await savePendingSync();
    return;
  }

  await syncData();
}
```

### 3. **Progress Feedback**
```javascript
const syncWithProgress = async (onProgress) => {
  const updates = await fetchUpdates();

  if (!updates.has_updates) return;

  const total = updates.events.length;

  for (let i = 0; i < total; i++) {
    await processEvent(updates.events[i]);
    onProgress((i + 1) / total * 100);
  }
};

// الاستخدام
syncWithProgress((progress) => {
  console.log(`Progress: ${progress}%`);
  updateProgressBar(progress);
});
```

---

**جميع الأمثلة جاهزة للاستخدام! 🚀**
