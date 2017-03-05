import logging

from pyswagger import App, Security
from pyswagger.contrib.client.requests import Client
# pyswagger makes INFO level logs regularly by default, so lower its logging
# level to prevent the spam.
logging.getLogger("pyswagger").setLevel(logging.WARNING)


log = logging.getLogger(__name__)


def main(schema_path):
    # Load Swagger schema.
    app = App.create(schema_path)

    log.debug("App paths: %r", app.root.paths)

    paths = app.root.paths.keys()
    log.info("Found paths as: %s", paths)

    # client = Client(Security(app))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main('http://127.0.0.1:5000/api/schema')
