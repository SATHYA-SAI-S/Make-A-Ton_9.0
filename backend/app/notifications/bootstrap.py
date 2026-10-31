from backend.app.shared.registry import register_port
from backend.app.notifications.service import NotificationService

def bootstrap():
    service = NotificationService()
    register_port("notification", service)
