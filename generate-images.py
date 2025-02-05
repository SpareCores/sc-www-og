from hashlib import sha1
import logging
import os

import sc_data
from html2image import Html2Image
from sc_crawler.tables import BenchmarkScore, Server
from sqlmodel import Session, create_engine, func, select

logging.getLogger().setLevel(logging.DEBUG)

IMAGE_FOLDER = os.environ.get("IMAGE_FOLDER", default="images")
os.makedirs(IMAGE_FOLDER, exist_ok=True)

BROWSER = os.environ.get("BROWSER", default="chrome")
SC_WWW_URL = os.environ.get("SC_WWW_URL", default="https://sparecores.com")

# list all servers
engine = create_engine(f"sqlite:///{sc_data.db.path}")
session = Session(engine)

max_scores = (
    select(
        BenchmarkScore.vendor_id,
        BenchmarkScore.server_id,
        func.max(BenchmarkScore.score).label("max_score"),
    )
    .where(BenchmarkScore.benchmark_id == "stress_ng:cpu_all")
    .group_by(BenchmarkScore.vendor_id, BenchmarkScore.server_id)
    .subquery()
)
servers = session.exec(
    select(
        Server.vendor_id,
        Server.api_reference,
        # main params to keep track of changes
        Server.description,
        Server.vcpus,
        Server.memory_amount,
        Server.gpu_count,
        Server.storage_size,
        max_scores.c.max_score,
    ).join(
        max_scores,
        (Server.vendor_id == max_scores.c.vendor_id)
        & (Server.server_id == max_scores.c.server_id),
        isouter=True,
    )
).all()

# init screenshot tool
hti = Html2Image(
    browser_executable=BROWSER,
    size=(1200, 630),
    custom_flags=[
        "--no-sandbox",
        "--hide-scrollbars",
        "--virtual-time-budget=500000",
    ],
)

for server in servers:
    logging.info(server)
    folder = os.path.join(IMAGE_FOLDER, server[0])
    os.makedirs(folder, exist_ok=True)
    digest = sha1(repr(server).encode("utf-8")).hexdigest()
    digest_path = os.path.join(folder, server[1] + ".digest")
    if os.path.exists(digest_path):
        if digest == open(digest_path, "r").read():
            logging.debug("Skipping as already generated before with the same content.")
            continue
    hti.output_path = folder
    hti.screenshot(
        url=f"{SC_WWW_URL}/og/{server[0]}/{server[1]}",
        save_as=server[1] + ".png",
    )
    open(digest_path, "w").write(digest)
