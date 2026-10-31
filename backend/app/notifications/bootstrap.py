from app.shared.registry import register_port
from app.notifications.service import NotificationService

def bootstrap():
    service = NotificationService()
    register_port("notification", service)
