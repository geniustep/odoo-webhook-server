from odoo import models, fields, api  # type: ignore
import logging

_logger = logging.getLogger(__name__)


class UserSyncState(models.Model):
    """Track sync state per user/device for multi-user sync support"""

    _name = "user.sync.state"
    _description = "User Sync State - Track last sync per user/device"
    _order = "last_sync_time desc"

    user_id = fields.Many2one(
        'res.users',
        string="User",
        required=True,
        index=True,
        ondelete='cascade',
        help="The user who owns this sync state"
    )

    device_id = fields.Char(
        string="Device ID",
        required=True,
        index=True,
        help="Unique identifier for the device (e.g., mobile-android-abc123)"
    )

    app_type = fields.Selection(
        selection=[
            ('sales_app', 'Sales App'),
            ('delivery_app', 'Delivery App'),
            ('manager_app', 'Manager App'),
            ('warehouse_app', 'Warehouse App'),
            ('mobile_app', 'Mobile App'),
        ],
        string="App Type",
        required=True,
        help="Type of application using this sync state"
    )

    last_sync_time = fields.Datetime(
        string="Last Sync Time",
        required=True,
        default=fields.Datetime.now,
        index=True,
        help="Timestamp of the last successful sync"
    )

    last_event_id = fields.Integer(
        string="Last Event ID",
        default=0,
        help="ID of last processed event from update.webhook"
    )

    sync_count = fields.Integer(
        string="Sync Count",
        default=0,
        help="Total number of syncs performed"
    )

    is_active = fields.Boolean(
        string="Active",
        default=True,
        index=True,
        help="Inactive devices won't affect archiving logic"
    )

    # SQL Constraints
    _sql_constraints = [
        ('unique_user_device',
         'unique(user_id, device_id)',
         'One sync state per user per device is allowed!')
    ]

    @api.model
    def get_or_create_state(self, user_id, device_id, app_type):
        """Get existing sync state or create new one"""
        state = self.search([
            ('user_id', '=', user_id),
            ('device_id', '=', device_id)
        ], limit=1)

        if not state:
            state = self.create({
                'user_id': user_id,
                'device_id': device_id,
                'app_type': app_type,
                'last_event_id': 0,
                'sync_count': 0
            })
            _logger.info(f"✨ Created new sync state for user {user_id}, device {device_id}")

        return state

    def update_sync_state(self, last_event_id):
        """Update sync state after successful sync"""
        self.ensure_one()
        self.write({
            'last_event_id': last_event_id,
            'last_sync_time': fields.Datetime.now(),
            'sync_count': self.sync_count + 1
        })
        _logger.info(f"📱 Updated sync state for user {self.user_id.id}: event_id={last_event_id}")

    @api.model
    def get_active_users_count(self, since_days=7):
        """Get count of active users in the last N days"""
        from datetime import timedelta
        cutoff_date = fields.Datetime.now() - timedelta(days=since_days)

        count = self.search_count([
            ('last_sync_time', '>=', cutoff_date),
            ('is_active', '=', True)
        ])

        return count
