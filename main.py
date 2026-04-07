from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
import io
import json
import re
import httpx

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import Paragraph as Para
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

NAVY = HexColor("#001A40")
RED = HexColor("#FF4040")
BLUE = HexColor("#50B0FF")
LIGHT_BLUE = HexColor("#A6DEFF")
GRAY = HexColor("#888888")
DARK_GRAY = HexColor("#444444")
DIVIDER = HexColor("#e0e0e0")

LEGAL_TEXT = (
    "Notices. Everett Financial, Inc. dba Supreme Lending, NMLS ID #2129 "
    "(www.nmlsconsumeraccess.org), 14801 Quorum Drive, Suite 300, Dallas, TX 75254 "
    "(877-350-5225). Solicitations made to and applications accepted from residents in "
    "AL, AK, AZ, AR, CA, CO, CT, DE, DC, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, "
    "MD, MA, MI, MN, MS, MO, MT, NE, NH, NJ, NM, NC, ND, NV, NY, OH, OK, OR, PA, PR, "
    "RI, SC, SD, TN, TX, UT, VT, VA, WA, WV, WI, WY. This is not an offer to enter into "
    "an agreement. Information, rates, and programs are subject to change without prior "
    "notice and may not be available in all states. All loans are subject to credit and "
    "property approval. Supreme Lending is not affiliated with any government agency. "
    "\u00a9 2026. Everett Financial, Inc. dba Supreme Lending. All rights reserved. "
    "Equal Housing Opportunity Lender."
)


def bytes_to_image_reader(data: bytes) -> ImageReader:
    img = PILImage.open(io.BytesIO(data))
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=90)
    out.seek(0)
    return ImageReader(out)


def draw_flyer(d: dict) -> bytes:
    # Sanitize all string fields
    for key in ["address", "price", "bedrooms", "bathrooms", "description",
                "open_house", "realtor_name", "realtor_title", "realtor_direct",
                "realtor_cell", "realtor_website", "realtor_email", "lo_name",
                "lo_nmls", "lo_direct", "lo_cell", "lo_website", "lo_email", "lo_address"]:
        if d.get(key) is None:
            d[key] = ""

    buf = io.BytesIO()
    W, H = letter
    c = canvas.Canvas(buf, pagesize=letter)
    margin = 0.35 * inch
    content_w = W - 2 * margin

    # HERO IMAGE
    hero_h = 3.0 * inch
    hero_reader = bytes_to_image_reader(d["hero_bytes"])
    c.drawImage(hero_reader, 0, H - hero_h, W, hero_h, preserveAspectRatio=False)

    # Price box overlay
    box_w = 1.6 * inch
    box_h = 0.78 * inch
    c.setFillColor(NAVY)
    c.rec
