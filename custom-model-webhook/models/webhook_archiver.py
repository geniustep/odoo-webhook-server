from odoo import models, fields, api  # type: ignore
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class WebhookArchiver(models.Model):
    """Automatic archiving of webhook events with smart rules"""

    _name = 'webhook.archiver'
    _description = 'Auto Archive Webhook Events'

    @api.model
    def auto_archive(self):
        """
        Smart archiving strategy:
        - Rule 1: Archive events older than 7 days if all active users synced
        - Rule 2: Force archive events older than 30 days (even if not all synced)
        - Rule 3: Delete archived events older than 90 days
        """

        now = fields.Datetime.now()
        archived_count = 0
        force_archived_count = 0
        deleted_count = 0

        # ========== Rule 1: Archive old events synced by all users ==========
        seven_days_ago = now - timedelta(days=7)

        # Get count of active users (synced in last 7 days)
        active_users_count = self.env['user.sync.state'].get_active_users_count(since_days=7)

        _logger.info(f"🔍 Auto Archive: Found {active_users_count} active users in last 7 days")

        if active_users_count > 0:
            # Find events that:
            # - Are older than 7 days
            # - Not archived yet
            # - Synced by all active users
            events_to_archive = self.env['update.webhook'].search([
                ('timestamp', '<=', seven_days_ago),
                ('is_archived', '=', False),
                ('min_users_synced', '>=', active_users_count),
            ])

            if events_to_archive:
                events_to_archive.archive_events()
                archived_count = len(events_to_archive)
                _logger.info(f"📦 Archived {archived_count} events (>7 days, all users synced)")

        # ========== Rule 2: Force archive very old events ==========
        thirty_days_ago = now - timedelta(days=30)

        very_old_events = self.env['update.webhook'].search([
            ('timestamp', '<=', thirty_days_ago),
            ('is_archived', '=', False),
        ])

        if very_old_events:
            very_old_events.archive_events()
            force_archived_count = len(very_old_events)
            _logger.info(f"📦 Force archived {force_archived_count} events (>30 days old)")

        # ========== Rule 3: Delete very old archived events ==========
        ninety_days_ago = now - timedelta(days=90)

        to_delete = self.env['update.webhook'].search([
            ('is_archived', '=', True),
            ('archive_date', '<=', ninety_days_ago),
        ])

        if to_delete:
            deleted_count = len(to_delete)
            to_delete.unlink()
            _logger.info(f"🗑️ Deleted {deleted_count} archived events (>90 days)")

        # ========== Clean inactive sync states ==========
        # Remove sync states for users inactive for more than 30 days
        inactive_states = self.env['user.sync.state'].search([
            ('last_sync_time', '<=', thirty_days_ago),
            ('is_active', '=', True),
        ])

        if inactive_states:
            inactive_states.write({'is_active': False})
            _logger.info(f"💤 Marked {len(inactive_states)} sync states as inactive")

        # Return summary
        return {
            'status': 'success',
            'archived_count': archived_count,
            'force_archived_count': force_archived_count,
            'deleted_count': deleted_count,
            'total_processed': archived_count + force_archived_count + deleted_count
        }

    @api.model
    def get_archive_stats(self):
        """Get archiving statistics"""

        webhook_model = self.env['update.webhook']

        total = webhook_model.search_count([])
        active = webhook_model.search_count([('is_archived', '=', False)])
        archived = webhook_model.search_count([('is_archived', '=', True)])

        # Oldest unarchived event
        oldest = webhook_model.search([('is_archived', '=', False)], order='timestamp asc', limit=1)
        oldest_date = oldest.timestamp if oldest else None

        return {
            'total_events': total,
            'active_events': active,
            'archived_events': archived,
            'oldest_unarchived': oldest_date,
            'archive_percentage': round((archived / total * 100) if total > 0 else 0, 2)
        }

    @api.model
    def force_archive_by_model(self, model_name, before_date=None):
        """Force archive events for a specific model"""

        domain = [
            ('model', '=', model_name),
            ('is_archived', '=', False),
        ]

        if before_date:
            domain.append(('timestamp', '<=', before_date))

        events = self.env['update.webhook'].search(domain)

        if events:
            events.archive_events()
            _logger.info(f"📦 Force archived {len(events)} events for model {model_name}")
            return len(events)

        return 0
