ModuleNotFoundError: No module named 'keyboards.admin_keyboard'; 'keyboards' is not a package
  File "/app/handlers/admin_panel.py", line 6, in <module>
    from keyboards.admin_keyboard import admin_menu
  File "/app/bot.py", line 500, in <module>
    from handlers.admin_panel import (
        router as admin_router
    )
Traceback (most recent call last):
Mounting volume on: /var/lib/containers/railwayapp/bind-mounts/0d5c1a79-5e35-41b7-88b6-78c5e86df44b/vol_p7j97ao23if057il
Traceback (most recent call last):
  File "/app/bot.py", line 500, in <module>
    from handlers.admin_panel import (
        router as admin_router
    )
  File "/app/handlers/admin_panel.py", line 6, in <module>
    from keyboards.admin_keyboard import admin_menu
ModuleNotFoundError: No module named 'keyboards.admin_keyboard'; 'keyboards' is not a package