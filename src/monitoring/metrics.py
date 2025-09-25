"""
Prometheus metrics for monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps

# Define metrics
email_processed_total = Counter(
    'email_processed_total',
    'Total number of emails processed',
    ['intent', 'priority', 'status']
)

email_processing_duration = Histogram(
    'email_processing_duration_seconds',
    'Time spent processing emails',
    ['intent']
)

active_connections = Gauge(
    'active_websocket_connections',
    'Number of active WebSocket connections'
)

knowledge_base_size = Gauge(
    'knowledge_base_documents_total',
    'Total documents in knowledge base',
    ['source']
)

api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

system_info = Info(
    'workflow_agent_info',
    'System information'
)

# Decorators for metrics
def track_processing_time(intent_extractor):
    """Decorator to track email processing time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            intent = intent_extractor(result) if callable(intent_extractor) else intent_extractor
            email_processing_duration.labels(intent=intent).observe(duration)
            
            return result
        return wrapper
    return decorator

def track_api_request(func):
    """Decorator to track API requests"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request info from FastAPI
        request = kwargs.get('request')
        if request:
            method = request.method
            endpoint = request.url.path
        else:
            method = 'UNKNOWN'
            endpoint = 'UNKNOWN'
        
        try:
            response = await func(*args, **kwargs)
            status_code = getattr(response, 'status_code', 200)
        except Exception as e:
            status_code = 500
            raise
        finally:
            api_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
        
        return response
    return wrapper

# Update system info
system_info.info({
    'version': '2.0.0',
    'environment': 'production'
})
