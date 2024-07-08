import logging
import os

import sc_data
from html2image import Html2Image
from sc_crawler.tables import Server
from sqlmodel import Session, create_engine, select

logging.basicConfig(level=logging.DEBUG)

IMAGE_FOLDER = os.environ.get("IMAGE_FOLDER", default="images")
os.makedirs(IMAGE_FOLDER, exist_ok=True)

BROWSER = os.environ.get("BROWSER", default="chrome")
SC_WWW_URL = os.environ.get("SC_WWW_URL", default="https://sparecores.com")

# list all servers
engine = create_engine(f"sqlite:///{sc_data.db.path}")
session = Session(engine)
servers = session.exec(select(Server.vendor_id, Server.api_reference)).all()

# init screenshot tool
hti = Html2Image(
    browser_executable=BROWSER,
    size=(1200, 630),
    custom_flags=[
        "--virtual-time-budget=500000",
    ],
)

for server in servers:
    logging.info(server)
    folder = os.path.join(IMAGE_FOLDER, server[0])
    os.makedirs(folder, exist_ok=True)
    filename = f"{server[1]}.png"
    if os.path.exists(os.path.join(folder, filename)):
        logging.debug("Skipping as already generated before.")
    else:
        hti.output_path = folder
        hti.screenshot(
            url=f"{SC_WWW_URL}/og/{server[0]}/{server[1]}",
            save_as=filename,
        )
