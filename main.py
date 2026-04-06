from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional
import io
import base64
import weasyprint

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LEGAL_TEXT = (
    "Notices. Everett Financial, Inc. dba Supreme Lending, NMLS ID #2129 (www.nmlsconsumeraccess.org), "
    "14801 Quorum Drive, Suite 300, Dallas, TX 75254 (877-350-5225). Solicitations made to and applications "
    "accepted from residents in AL, AK, AZ, AR, CA: Licensed by the Department of Financial Protection and "
    "Innovation under the California Residential Mortgage Lending Act; CO, CT, DE, DC, FL, GA, Hawaii Mortgage "
    "Loan Originator Company License HI2129, Mortgage Servicer License MS144, ID, IL, IN, IA, KS, KY, LA, ME, "
    "MD, MA: MA Mortgage Broker License MC2129, MA Mortgage Lender License MC2129, MA Mortgage Servicer License "
    "LS2129; MI, MN, MS, MO, MT, NE, NH, NJ: Licensed by the N.J. Department of Banking and Insurance; NM, NC, "
    "ND, NV, Licensed Mortgage Banker -- NYS Banking Department, NY Office: 6325 Sheridan Drive, Suite 1 Buffalo, "
    "NY 14221, OH, OK, OR, PA, PR, RI, SC, SD, TN, TX, UT, VT, VA, WA, WV, WI, WY. This is not an offer to enter "
    "into an agreement. Information, rates, and programs are subject to change without prior notice and may not be "
    "available in all states. All loans are subject to credit and property approval. Supreme Lending is not "
    "affiliated with any government agency. \u00a9 2026. Everett Financial, Inc. dba Supreme Lending. All rights "
    "reserved. Equal Housing Opportunity Lender."
)

SL_LOGO_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1366 282.75">
  <defs><style>.c1{fill:#ff2b46}.c2{fill:#001d49}</style></defs>
  <g>
    <path class="c2" d="M13.46,155.65h15.12c.45,7.61,5.15,13.66,16.91,13.66,9.97,0,15.45-4.25,15.45-11.31,0-6.38-4.37-9.18-12.21-10.75l-10.75-2.13c-12.77-2.46-22.4-8.4-22.4-21.62,0-14.45,11.54-22.4,29.45-22.4s29.34,8.18,29.34,23.29h-15.12c0-7.17-5.6-10.97-14.56-10.97-9.97,0-13.66,4.7-13.66,10.08,0,4.37,2.69,8.18,10.53,9.86l10.08,2.02c17.47,3.47,24.86,10.3,24.86,22.51,0,16.13-13.22,23.74-31.13,23.74-20.05,0-31.92-9.63-31.92-25.98Z"/>
    <path class="c2" d="M89.18,150.84v-48.71h14.78v47.59c0,12.54,6.27,19.04,16.91,19.04s16.8-6.49,16.8-19.04v-47.59h14.89v48.71c0,20.5-12.88,30.8-31.69,30.8s-31.69-10.3-31.69-30.8Z"/>
    <path class="c2" d="M166.92,102.12h30.8c20.16,0,29.34,10.41,29.34,25.65s-9.18,25.53-29.34,25.53h-16.13v27.21h-14.67v-78.39ZM211.94,127.77c0-7.95-4.7-12.77-14.78-12.77h-15.57v25.42h15.57c10.08,0,14.78-4.82,14.78-12.66Z"/>
    <path class="c2" d="M238.49,102.12h30.8c20.16,0,29.34,10.41,29.34,25.65,0,11.31-5.15,20.04-16.35,23.63l17.02,29.12h-14.67l-15.57-27.21h-15.9v27.21h-14.67v-78.39ZM283.51,127.77c0-7.95-4.7-12.77-14.78-12.77h-15.57v25.42h15.57c10.08,0,14.78-4.82,14.78-12.66Z"/>
    <path class="c2" d="M310.85,102.12h52.52v12.88h-37.85v19.94h34.49v11.53h-34.49v21.17h38.97v12.88h-53.64v-78.39Z"/>
    <path class="c2" d="M375.92,102.12h18.37l22.85,58.57,22.85-58.57h18.37v78.39h-14.67v-52.64h-.56l-20.38,52.64h-11.2l-20.49-52.64h-.45v52.64h-14.67v-78.39Z"/>
    <path class="c2" d="M473.14,102.12h52.52v12.88h-37.85v19.94h34.49v11.53h-34.49v21.17h38.97v12.88h-53.64v-78.39Z"/>
  </g>
  <g>
    <path class="c2" d="M889.39,102.12h14.67v65.51h37.18v12.88h-51.85v-78.39Z"/>
    <path class="c2" d="M952.68,102.12h52.52v12.88h-37.85v19.94h34.49v11.53h-34.49v21.17h38.97v12.88h-53.64v-78.39Z"/>
    <path class="c2" d="M1017.76,102.12h15.45l34.27,54.99h.34v-54.99h14.78v78.39h-16.13l-33.71-54.09h-.34v54.09h-14.67v-78.39Z"/>
    <path class="c2" d="M1097.39,102.12h28.45c24.53,0,37.07,14.11,37.07,39.2s-12.54,39.2-37.07,39.2h-28.45v-78.39ZM1147.9,141.32c0-18.25-6.38-26.32-23.52-26.32h-12.32v52.64h12.32c17.13,0,23.52-8.06,23.52-26.32Z"/>
    <path class="c2" d="M1175.58,102.12h14.67v78.39h-14.67v-78.39Z"/>
    <path class="c2" d="M1205.03,102.12h15.45l34.27,54.99h.34v-54.99h14.78v78.39h-16.13l-33.71-54.09h-.34v54.09h-14.67v-78.39Z"/>
    <path class="c2" d="M1282.43,141.65c0-26.09,14.33-40.54,36.06-40.54,16.01,0,29.68,7.84,32.25,24.53h-14.67c-2.46-8.96-10.08-11.76-17.58-11.76-14.78,0-21.28,11.09-21.28,27.33s6.72,27.66,21.5,27.66c9.86,0,19.15-5.04,19.15-18.81h-16.35v-11.87h31.02v7.39c0,23.74-12.66,36.06-33.82,36.06-23.07,0-36.28-14.78-36.28-39.98Z"/>
  </g>
  <path class="c1" d="M708.09,8.42c-73.43,0-132.96,59.53-132.96,132.96s59.53,132.96,132.96,132.96,132.96-59.53,132.96-132.96S781.52,8.42,708.09,8.42ZM787.39,209.19h-158.6v-16.49h139.21v-38.56h-109.53v-17.81h128.92v72.87ZM648.2,126.04v38.37h109.53v18h-128.94v-56.45h-23.64l102.95-79.94,102.93,79.94-162.83.08Z"/>
</svg>'''

EQUAL_HOUSING_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="none" stroke="#000" stroke-width="4"/>
  <polygon points="50,10 90,45 80,45 80,85 60,85 60,60 40,60 40,85 20,85 20,45 10,45" fill="#000"/>
  <rect x="35" y="70" width="30" height="4" fill="#000"/>
  <rect x="35" y="78" width="30" height="4" fill="#000"/>
</svg>'''


def file_to_b64(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def detect_mime(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    return {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml"}.get(ext, "image/jpeg")


def build_html(d: dict) -> str:
    open_house_row = ""
    if d.get("open_house"):
        open_house_row = f'<div class="open-house">OPEN HOUSE &nbsp;|&nbsp; {d["open_house"].upper()}</div>'

    realtor_direct = f'<div class="ci-line">Direct: {d["realtor_direct"]}</div>' if d.get("realtor_direct") else ""
    realtor_cell = f'<div class="ci-line">Cell: {d["realtor_cell"]}</div>' if d.get("realtor_cell") else ""
    realtor_website = f'<div class="ci-line ci-link">{d["realtor_website"]}</div>' if d.get("realtor_website") else ""
    realtor_email = f'<div class="ci-line ci-link">{d["realtor_email"]}</div>' if d.get("realtor_email") else ""
    realtor_company = f'<div class="ci-line">{d["realtor_company"]}</div>' if d.get("realtor_company") else ""

    lo_direct = f'<div class="ci-line">Direct: {d["lo_direct"]}</div>' if d.get("lo_direct") else ""
    lo_cell = f'<div class="ci-line">Cell: {d["lo_cell"]}</div>' if d.get("lo_cell") else ""
    lo_website = f'<div class="ci-line ci-link">{d["lo_website"]}</div>' if d.get("lo_website") else ""
    lo_email = f'<div class="ci-line ci-link">{d["lo_email"]}</div>' if d.get("lo_email") else ""
    lo_address = f'<div class="ci-line">{d["lo_address"]}</div>' if d.get("lo_address") else ""

    realtor_logo_html = ""
    if d.get("realtor_logo_b64"):
        realtor_logo_html = f'<img class="realtor-logo" src="{d["realtor_logo_b64"]}" />'

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,400;0,600;0,700;0,800;0,900;1,600;1,700&display=swap');

* {{ margin:0; padding:0; box-sizing:border-box; }}

html, body {{
  width: 8.5in;
  height: 11in;
  font-family: 'Montserrat', sans-serif;
  background: white;
  overflow: hidden;
}}

.page {{
  width: 8.5in;
  height: 11in;
  display: flex;
  flex-direction: column;
}}

/* ── Hero ── */
.hero {{
  position: relative;
  width: 100%;
  height: 3.05in;
  flex-shrink: 0;
  background: #0a1e3c;
}}

.hero-img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}}

.price-box {{
  position: absolute;
  top: 0;
  left: 0;
  background: rgba(10, 30, 60, 0.88);
  color: white;
  padding: 10px 18px 12px;
  min-width: 1.6in;
}}

.price-box .price {{
  font-size: 26pt;
  font-weight: 800;
  color: white;
  line-height: 1;
}}

.price-box .prop-detail {{
  font-size: 10pt;
  font-weight: 600;
  color: white;
  line-height: 1.5;
}}

/* ── Address Bar ── */
.address-bar {{
  background: #c2d9ed;
  padding: 10px 28px 8px;
  flex-shrink: 0;
  border-radius: 0 0 8px 8px;
}}

.address-bar .address {{
  font-size: 21pt;
  font-weight: 900;
  color: #0a1e3c;
  line-height: 1.15;
  letter-spacing: -0.01em;
}}

.open-house {{
  font-size: 10.5pt;
  font-weight: 700;
  color: #0a1e3c;
  letter-spacing: 0.04em;
  margin-top: 2px;
}}

/* ── Interior Photos ── */
.photo-row {{
  display: flex;
  gap: 5px;
  padding: 8px 10px 6px;
  flex-shrink: 0;
}}

.photo-row img {{
  flex: 1;
  height: 1.3in;
  object-fit: cover;
  display: block;
  border-radius: 2px;
}}

/* ── Description ── */
.description {{
  padding: 4px 28px 6px;
  font-size: 8pt;
  line-height: 1.55;
  text-align: justify;
  color: #1a1a1a;
  flex-shrink: 0;
}}

/* ── Divider ── */
.divider {{
  border: none;
  border-top: 1px solid #d0d0d0;
  margin: 5px 24px;
  flex-shrink: 0;
}}

/* ── Contact Section ── */
.contact-section {{
  display: flex;
  padding: 4px 22px 0;
  gap: 16px;
  flex-shrink: 0;
}}

.contact-col {{
  flex: 1;
}}

.contact-header {{
  font-style: italic;
  font-size: 10.5pt;
  color: #222;
  font-weight: 600;
  margin-bottom: 6px;
}}

.contact-header .today {{
  color: #e84040;
  font-style: italic;
  font-weight: 700;
}}

.contact-body {{
  display: flex;
  gap: 10px;
  align-items: flex-start;
}}

.contact-headshot {{
  width: 0.88in;
  height: 0.88in;
  object-fit: cover;
  object-position: top center;
  flex-shrink: 0;
  border-radius: 2px;
}}

.contact-info .ci-name {{
  font-size: 10.5pt;
  font-weight: 800;
  color: #0a1e3c;
  line-height: 1.3;
}}

.contact-info .ci-line {{
  font-size: 7.8pt;
  color: #222;
  line-height: 1.55;
}}

.contact-info .ci-link {{
  color: #1a5fa8;
}}

/* ── Logo Row ── */
.logo-row {{
  display: flex;
  padding: 6px 22px 4px;
  align-items: center;
  flex-shrink: 0;
}}

.logo-col {{
  flex: 1;
  display: flex;
  align-items: center;
}}

.realtor-logo {{
  max-height: 0.62in;
  max-width: 2.4in;
  object-fit: contain;
}}

.sl-logo-wrap svg {{
  height: 0.5in;
  width: auto;
}}

/* ── Legal Footer ── */
.legal {{
  padding: 3px 22px 4px;
  font-size: 4.8pt;
  color: #444;
  line-height: 1.45;
  display: flex;
  align-items: flex-start;
  gap: 6px;
  flex-shrink: 0;
  margin-top: auto;
}}

.eq-housing {{
  width: 20px;
  min-width: 20px;
  margin-top: 1px;
}}
</style>
</head>
<body>
<div class="page">

  <!-- Hero -->
  <div class="hero">
    <img class="hero-img" src="{d['hero_b64']}" />
    <div class="price-box">
      <div class="price">${d['price']}</div>
      <div class="prop-detail">{d['bedrooms']} Bedrooms</div>
      <div class="prop-detail">{d['bathrooms']} Bathrooms</div>
    </div>
  </div>

  <!-- Address Bar -->
  <div class="address-bar">
    <div class="address">{d['address']}</div>
    {open_house_row}
  </div>

  <!-- Interior Photos -->
  <div class="photo-row">
    <img src="{d['photo2_b64']}" />
    <img src="{d['photo3_b64']}" />
    <img src="{d['photo4_b64']}" />
  </div>

  <!-- Description -->
  <div class="description">{d['description']}</div>

  <!-- Divider -->
  <hr class="divider" />

  <!-- Contact Section -->
  <div class="contact-section">

    <!-- Realtor -->
    <div class="contact-col">
      <div class="contact-header"><em>Call <span class="today">Today</span> for Property Information</em></div>
      <div class="contact-body">
        <img class="contact-headshot" src="{d['realtor_headshot_b64']}" />
        <div class="contact-info">
          <div class="ci-name">{d['realtor_name']}</div>
          <div class="ci-line">{d['realtor_title']}</div>
          {realtor_company}
          {realtor_direct}
          {realtor_cell}
          {realtor_website}
          {realtor_email}
        </div>
      </div>
    </div>

    <!-- LO -->
    <div class="contact-col">
      <div class="contact-header"><em>Call <span class="today">Today</span> for Mortgage Information</em></div>
      <div class="contact-body">
        <img class="contact-headshot" src="{d['lo_headshot_b64']}" />
        <div class="contact-info">
          <div class="ci-name">{d['lo_name']}</div>
          <div class="ci-line">Loan Officer NMLS#{d['lo_nmls']}</div>
          {lo_direct}
          {lo_cell}
          {lo_website}
          {lo_email}
          {lo_address}
        </div>
      </div>
    </div>

  </div>

  <!-- Logo Row -->
  <div class="logo-row">
    <div class="logo-col">
      {realtor_logo_html}
    </div>
    <div class="logo-col">
      <div class="sl-logo-wrap">{SL_LOGO_SVG}</div>
    </div>
  </div>

  <!-- Legal Footer -->
  <div class="legal">
    <svg class="eq-housing" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 110">
      <rect x="2" y="2" width="96" height="96" fill="none" stroke="#333" stroke-width="5"/>
      <polygon points="50,8 92,44 82,44 82,90 60,90 60,65 40,65 40,90 18,90 18,44 8,44" fill="#333"/>
      <rect x="30" y="98" width="40" height="6" fill="#333"/>
    </svg>
    <div>{LEGAL_TEXT}</div>
  </div>

</div>
</body>
</html>"""


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
        def b64(f): 
            data = f
            mime = detect_mime(f.filename) if hasattr(f, 'filename') else "image/jpeg"
            return file_to_b64(data, mime)

        async def read_b64(f: UploadFile):
            data = await f.read()
            return file_to_b64(data, detect_mime(f.filename))

        d = {
            "address": address,
            "price": price,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "description": description,
            "open_house": open_house,
            "realtor_name": realtor_name,
            "realtor_title": realtor_title,
            "realtor_company": realtor_company,
            "realtor_direct": realtor_direct,
            "realtor_cell": realtor_cell,
            "realtor_website": realtor_website,
            "realtor_email": realtor_email,
            "lo_name": lo_name,
            "lo_nmls": lo_nmls,
            "lo_direct": lo_direct,
            "lo_cell": lo_cell,
            "lo_website": lo_website,
            "lo_email": lo_email,
            "lo_address": lo_address,
            "hero_b64": await read_b64(hero_photo),
            "photo2_b64": await read_b64(photo2),
            "photo3_b64": await read_b64(photo3),
            "photo4_b64": await read_b64(photo4),
            "realtor_headshot_b64": await read_b64(realtor_headshot),
            "lo_headshot_b64": await read_b64(lo_headshot),
            "realtor_logo_b64": await read_b64(realtor_logo) if realtor_logo and realtor_logo.filename else None,
        }

        html = build_html(d)
        pdf_bytes = weasyprint.HTML(string=html, base_url=None).write_pdf()

        safe_address = address.replace(",", "").replace(" ", "_")[:40]
        filename = f"OpenHouse_{safe_address}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating flyer: {str(e)}")


@app.get("/health")
def health():
    return {"status": "ok"}
