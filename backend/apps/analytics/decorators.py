import functools
import time
import logging
from .models import AiLog

logger = logging.getLogger(__name__)

def track_ai_performance(tier, operation='other'):
    """
    Decorator to track AI client performance.
    Usage:
    @track_ai_performance('gemini', 'extraction')
    def my_func(self, ...): 
        ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            tokens = 0
            
            try:
                result = func(*args, **kwargs)
                
                # Try to extract usage info if available in result result
                # This depends on client returning a dict with usage, or just result
                # Current clients return dict or list, or None. 
                # If it returns None, success might be False depending on logic, but here we assume no exception = technical success.
                
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise e
            finally:
                duration = int((time.time() - start_time) * 1000)
                
                # Defensive DB write
                try:
                    AiLog.objects.create(
                        tier=tier,
                        operation=operation,
                        duration_ms=duration,
                        success=success,
                        error_message=error_message,
                        tokens_used=tokens # Will be 0 for now as clients don't return usage uniformly
                    )
                except Exception as db_e:
                    logger.error(f"Failed to log AI metric: {db_e}")
                    
        return wrapper
    return decorator
