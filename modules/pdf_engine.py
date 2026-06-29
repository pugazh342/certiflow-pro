# modules/pdf_engine.py
import re
import sys
import asyncio
from pathlib import Path
from typing import Dict, Tuple
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
import config

class PDFRenderer:
    def __init__(self):
        self.jinja_env = Environment(loader=FileSystemLoader(str(config.TEMPLATE_DIR)))
        self.template = self.jinja_env.get_template("base_cert.html")

    def _sanitize_filename(self, name: str) -> str:
        clean = re.sub(r"[^\w\s-]", "", name).strip()
        return re.sub(r"[-\s]+", "_", clean)

    def generate_html(self, record: Dict[str, str]) -> str:
        name = record.get("Name", "Recipient")
        font_size = (
            config.NORMAL_FONT_SIZE_PX 
            if len(name) <= config.MAX_NAME_LEN_NORMAL_FONT 
            else config.SCALED_FONT_SIZE_PX
        )
        
        context = {**record, "dynamic_font_size": f"{font_size}px"}
        return self.template.render(context)

    async def render_pdf_async(self, record: Dict[str, str]) -> Tuple[bool, str]:
        try:
            html_content = self.generate_html(record)
            safe_name = self._sanitize_filename(record.get("Name", "Cert"))
            rec_id = record.get("_record_id", "0")
            output_path = config.PDF_OUTPUT_DIR / f"{rec_id}_{safe_name}.pdf"

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_content(html_content, wait_until="networkidle")
                await page.pdf(
                    path=str(output_path),
                    format="A4",
                    landscape=True,
                    print_background=True,
                    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
                )
                await browser.close()

            return True, str(output_path)
        except Exception as e:
            return False, f"Render exception: {str(e)}"

def render_certificate(record: Dict[str, str]) -> Tuple[bool, str]:
    """Synchronous wrapper for async Playwright pipeline."""
    
    # --- WINDOWS ASYNCIO FIX ---
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    # ---------------------------
    
    renderer = PDFRenderer()
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(renderer.render_pdf_async(record))