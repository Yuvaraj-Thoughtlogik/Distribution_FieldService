import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Configure the company/accounting and load the transactional demo data.

    Everything is idempotent, so the same entry point is exposed as a server action
    ("Reload All Demo Data") and can be re-run safely.
    """
    _logger.info("tl_dfs_demo_data: loading configuration and sample data")
    env["tl.dfs.demo.loader"].action_load_all()
