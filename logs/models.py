from datetime import datetime

class RequestLog:
    """
    Represents a single request log stored in MongoDB.
    Contains minimal schema-level validation.
    """

    def __init__(self, phone: str, ip: str = None, user_agent: str = None, pg_status: str = None, referrer: str = None,
                 request_id: str = None):
        self.phone = phone
        self.ip = ip
        self.user_agent = user_agent
        self.pg_status = pg_status
        self.created_at = datetime.utcnow()
        self.referrer = referrer
        self.request_id = request_id

    def to_dict(self) -> dict:
        """Convert log instance into a Mongo-friendly dictionary."""
        return {
            "phone": self.phone,
            "ip": self.ip,
            "user_agent": self.user_agent,
            "pg_status": self.pg_status,
            "created_at": self.created_at.isoformat(),
            "referrer": self.referrer,
            "request_id": self.request_id,
        }