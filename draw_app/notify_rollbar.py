import rollbar

from contextlib import contextmanager, asynccontextmanager
from django.conf import settings


@contextmanager
def notify_rollbar(level='error', extra_data=None):
    # initialization should be done before yield to avoid exception during report_message call
    # initialization should be even if rollbar token was now specified
    init_rollbar()

    try:
        yield
    except: # noqa
        rollbar.report_exc_info(level=level, extra_data=extra_data)
        raise
    finally:
        # FIXME should replace with async version
        # Avoid messages losing. Details are here https://docs.rollbar.com/docs/python#aws-lambda
        rollbar.wait()


@asynccontextmanager
async def anotify_rollbar(level='error', extra_data=None):
    # initialization should be done before yield to avoid exception during report_message call
    # initialization should be even if rollbar token was now specified
    init_rollbar()

    try:
        yield
    except: # noqa
        rollbar.report_exc_info(level=level, extra_data=extra_data)
        raise
    finally:
        # FIXME should replace with async version
        # Avoid messages losing. Details are here https://docs.rollbar.com/docs/python#aws-lambda
        rollbar.wait()


def init_rollbar():
    if not rollbar._initialized:
        rollbar.init(
            settings.ROLLBAR['access_token'],
            settings.ROLLBAR['environment'],
            root=settings.BASE_DIR,
            locals=settings.ROLLBAR['locals'],
            allow_logging_basic_config=False,
        )
