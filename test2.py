
# Put your real DSN here (or use env var for extra safety)
import sentry_sdk

sentry_sdk.init(
    dsn="https://7e57dd91c16a6461fb36e95a2f7500e1@o4510366813519872.ingest.us.sentry.io/4510370710224896",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)
ans = 22/0
print(ans)
