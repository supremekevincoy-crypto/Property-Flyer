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
    c.rect(0, H - box_h, box_w, box_h, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(10, H - 24, f"${d['price']}")
    c.setFont("Helvetica", 8.5)
    c.drawString(10, H - 37, f"{d['bedrooms']} Bedrooms")
    c.drawString(10, H - 49, f"{d['bathrooms']} Bathrooms")

    y = H - hero_h

    # ADDRESS BAR
    has_oh = bool(d.get("open_house", "").strip())
    addr_h = 0.78 * inch if has_oh else 0.6 * inch
    c.setFillColor(LIGHT_BLUE)
    c.rect(0, y - addr_h, W, addr_h, fill=1, stroke=0)

    addr = d["address"].upper()
    addr_fs = 17
    c.setFillColor(NAVY)
    while c.stringWidth(addr, "Helvetica-Bold", addr_fs) > content_w - 20 and addr_fs > 10:
        addr_fs -= 1
    c.setFont("Helvetica-Bold", addr_fs)
    if has_oh:
        c.drawCentredString(W / 2, y - addr_h + addr_h * 0.62, addr)
        c.setFont("Helvetica", 9)
        c.drawCentredString(W / 2, y - addr_h + addr_h * 0.22,
                           f"OPEN HOUSE  |  {d['open_house'].upper()}")
    else:
        c.drawCentredString(W / 2, y - addr_h + addr_h * 0.38, addr)

    y -= addr_h

    # INTERIOR PHOTOS
    photo_h = 1.28 * inch
    gap = 4
    photo_w = (W - 2 * gap) / 3
    for i, key in enumerate(["photo2_bytes", "photo3_bytes", "photo4_bytes"]):
        ph = d.get(key)
        if ph:
            try:
                pr = bytes_to_image_reader(ph)
                c.drawImage(pr, i * (photo_w + gap), y - photo_h,
                           photo_w, photo_h, preserveAspectRatio=False)
            except:
                pass
    y -= photo_h + 5

    # DESCRIPTION
    desc_style = ParagraphStyle(
        "desc", fontName="Helvetica", fontSize=7.5,
        textColor=DARK_GRAY, leading=11.5, alignment=TA_JUSTIFY,
    )
    desc_para = Para(d.get("description", ""), desc_style)
    _, desc_h = desc_para.wrap(content_w, 999)
    desc_para.drawOn(c, margin, y - desc_h - 4)
    y -= desc_h + 10

    # DIVIDER
    c.setStrokeColor(DIVIDER)
    c.setLineWidth(0.5)
    c.line(margin, y, W - margin, y)
    y -= 8

    # CONTACT SECTION
    col_w = content_w / 2
    hs = 0.7 * inch

    def draw_contact(x_off, name, title, direct, cell, website, email, hs_bytes, label):
        name = name or ""
        title = title or ""
        direct = direct or ""
        cell = cell or ""
        website = website or ""
        email = email or ""

        cx = margin + x_off
        c.setFont("Helvetica-BoldOblique", 8)
        c.setFillColor(DARK_GRAY)
        c.drawString(cx, y - 10, "Call ")
        w1 = c.stringWidth("Call ", "Helvetica-BoldOblique", 8)
        c.setFillColor(RED)
        c.drawString(cx + w1, y - 10, "Today")
        w2 = c.stringWidth("Today", "Helvetica-BoldOblique", 8)
        c.setFillColor(DARK_GRAY)
        c.drawString(cx + w1 + w2, y - 10, f" for {label}")

        if hs_bytes:
            try:
                hr = bytes_to_image_reader(hs_bytes)
                c.drawImage(hr, cx, y - 14 - hs, hs, hs, preserveAspectRatio=False)
            except:
                pass

        tx = cx + hs + 7
        ty = y - 22
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(NAVY)
        c.drawString(tx, ty, name)
        ty -= 11
        c.setFont("Helvetica", 7.5)
        c.setFillColor(DARK_GRAY)
        if title:
            c.drawString(tx, ty, title)
            ty -= 10
        if direct:
            c.drawString(tx, ty, f"Direct: {direct}")
            ty -= 10
        if cell:
            c.drawString(tx, ty, f"Cell: {cell}")
            ty -= 10
        c.setFillColor(BLUE)
        if website:
            c.drawString(tx, ty, website)
            ty -= 10
        if email:
            c.drawString(tx, ty, email)
            ty -= 10
        if d.get("lo_address") and label == "Mortgage Information":
            c.setFillColor(DARK_GRAY)
            addr_lines = d["lo_address"].split(",")
            for line in addr_lines[:2]:
                if line.strip():
                    c.drawString(tx, ty, line.strip())
                    ty -= 10

    draw_contact(0,
        d.get("realtor_name", ""), d.get("realtor_title", "REALTOR"),
        d.get("realtor_direct"), d.get("realtor_cell"),
        d.get("realtor_website"), d.get("realtor_email"),
        d.get("realtor_headshot_bytes"), "Property Information")

    draw_contact(col_w,
        d.get("lo_name", ""), f"Loan Officer NMLS#{d.get('lo_nmls', '')}",
        d.get("lo_direct"), d.get("lo_cell"),
        d.get("lo_website"), d.get("lo_email"),
        d.get("lo_headshot_bytes"), "Mortgage Information")

    y -= hs + 20

    # LOGO ROW
    if d.get("realtor_logo_bytes"):
        try:
            rl = bytes_to_image_reader(d["realtor_logo_bytes"])
            c.drawImage(rl, margin, y - 0.55 * inch,
                       1.3 * inch, 0.5 * inch, preserveAspectRatio=True)
        except:
            pass

    sl_x = W - margin - 1.85 * inch
    sl_y = y - 0.45 * inch
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(sl_x, sl_y + 18, "SUPREME")
    c.setFillColor(RED)
    c.circle(sl_x + 70, sl_y + 22, 9, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(sl_x + 70, sl_y + 19, "SL")
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(sl_x + 83, sl_y + 18, "LENDING")

    # LEGAL
    legal_style = ParagraphStyle(
        "legal", fontName="Helvetica", fontSize=4.3,
        textColor=GRAY, leading=6, alignment=TA_JUSTIFY,
    )
    legal_para = Para(LEGAL_TEXT, legal_style)
    _, lh = legal_para.wrap(content_w, 999)
    legal_para.drawOn(c, margin, 5)

    c.save()
    buf.seek(0)
    return buf.read()


@app.post("/fetch-property")
async def fetch_property(url: str = Form(...)):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(url, headers=headers)
            html = resp.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch page: {str(e)}")

    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html, re.DOTALL)
    if not match:
        raise HTTPException(status_code=422,
            detail="Could not find property data. Make sure it is a valid Zillow listing URL.")

    try:
        data = json.loads(match.group(1))
        props = data["props"]["pageProps"]
        home = None
        if "gdpClientCache" in props:
            cache = props["gdpClientCache"]
            first_key = next(iter(cache))
            home = cache[first_key].get("property") or cache[first_key]
        elif "homeDetails" in props:
            home = props["homeDetails"]
        elif "property" in props:
            home = props["property"]
        if not home:
            raise HTTPException(status_code=422, detail="Property data not found.")

        address_obj = home.get("address", {})
        full_address = ", ".join(filter(None, [
            address_obj.get("streetAddress"),
            address_obj.get("city"),
            f"{address_obj.get('state', '')} {address_obj.get('zipcode', '')}".strip()
        ]))
        price_raw = home.get("price") or home.get("listingPrice") or 0
        price = f"{int(price_raw):,}" if price_raw else ""
        beds = str(home.get("bedrooms") or home.get("beds") or "")
        baths_raw = home.get("bathrooms") or home.get("baths") or ""
        baths = str(int(float(baths_raw)) if baths_raw and float(baths_raw) == int(float(baths_raw)) else baths_raw)
        description = home.get("description") or ""

        photos = []
        for p in (home.get("photos") or home.get("originalPhotos") or []):
            if isinstance(p, dict):
                mixed = p.get("mixedSources", {})
                jpeg_list = mixed.get("jpeg") or mixed.get("webp") or []
                if jpeg_list:
                    best = jpeg_list[-1].get("url") or jpeg_list[0].get("url")
                    if best:
                        photos.append(best)
                elif p.get("url"):
                    photos.append(p["url"])

        return JSONResponse({
            "address": full_address,
            "price": price,
            "bedrooms": beds,
            "bathrooms": baths,
            "description": description,
            "photos": photos[:20],
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error parsing: {str(e)}")


@app.post("/generate")
async def generate_flyer(
    address: str = Form(...),
    price: str = Form(...),
    bedrooms: str = Form(...),
    bathrooms: str = Form(...),
    description: str = Form(...),
    open_house: Optional[str] = Form(None),
    realtor_name: str = Form(...),
    realtor_title: str = Form(...),
    realtor_company: Optional[str] = Form(None),
    realtor_direct: Optional[str] = Form(None),
    realtor_cell: Optional[str] = Form(None),
    realtor_website: Optional[str] = Form(None),
    realtor_email: Optional[str] = Form(None),
    lo_name: str = Form(...),
    lo_nmls: str = Form(...),
    lo_direct: Optional[str] = Form(None),
    lo_cell: Optional[str] = Form(None),
    lo_website: Optional[str] = Form(None),
    lo_email: Optional[str] = Form(None),
    lo_address: Optional[str] = Form(None),
    hero_photo: UploadFile = File(...),
    photo2: UploadFile = File(...),
    photo3: UploadFile = File(...),
    photo4: UploadFile = File(...),
    realtor_headshot: UploadFile = File(...),
    lo_headshot: UploadFile = File(...),
    realtor_logo: Optional[UploadFile] = File(None),
):
    try:
        d = {
            "address": address, "price": price,
            "bedrooms": bedrooms, "bathrooms": bathrooms,
            "description": description, "open_house": open_house,
            "realtor_name": realtor_name, "realtor_title": realtor_title,
            "realtor_company": realtor_company, "realtor_direct": realtor_direct,
            "realtor_cell": realtor_cell, "realtor_website": realtor_website,
            "realtor_email": realtor_email, "lo_name": lo_name, "lo_nmls": lo_nmls,
            "lo_direct": lo_direct, "lo_cell": lo_cell, "lo_website": lo_website,
            "lo_email": lo_email, "lo_address": lo_address,
            "hero_bytes": await hero_photo.read(),
            "photo2_bytes": await photo2.read(),
            "photo3_bytes": await photo3.read(),
            "photo4_bytes": await photo4.read(),
            "realtor_headshot_bytes": await realtor_headshot.read(),
            "lo_headshot_bytes": await lo_headshot.read(),
            "realtor_logo_bytes": await realtor_logo.read() if realtor_logo and realtor_logo.filename else None,
        }
        pdf_bytes = draw_flyer(d)
        safe_addr = address.replace(",", "").replace(" ", "_")[:40]
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="OpenHouse_{safe_addr}.pdf"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/health")
def health():
    return {"status": "ok"}
