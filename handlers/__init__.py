# Background
from .background import check_mute

# Routers
from .private import user_router, manager_router, admin_router
from .private import unknown_cmd
from .group import group_router

all_routers = [
    group_router,
    user_router, manager_router, admin_router,
    unknown_cmd.unk_router
]