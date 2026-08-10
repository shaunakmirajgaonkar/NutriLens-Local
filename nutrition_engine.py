import re
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
try: import pytesseract
except Exception: pytesseract=None

ALLERGENS={"milk":["milk","whey","casein","caseinate","lactose","cream","butter"],"soy":["soy","soya","soybean","soya lecithin"],"wheat/gluten":["wheat","gluten","barley","rye","malt"],"peanuts":["peanut","groundnut"],"tree nuts":["almond","cashew","walnut","hazelnut","pistachio","pecan"],"egg":["egg","albumin","mayonnaise"],"sesame":["sesame","tahini"],"fish":["fish","anchovy","tuna","salmon"],"shellfish":["shellfish","shrimp","crab","prawn"]}
RULES={"added sugar":["sugar","cane sugar","brown sugar","glucose syrup","corn syrup","fructose syrup","maltodextrin"],"refined oil":["palm oil","hydrogenated oil","partially hydrogenated","shortening"],"intense sweetener":["sucralose","aspartame","acesulfame","saccharin"],"preservative/additive signal":["sodium benzoate","potassium sorbate","bha","bht","sulfite"]}
def ocr_image(im):
    if pytesseract is None: raise RuntimeError("pytesseract is unavailable. Install it and local Tesseract, or use Text Reader.")
    im=ImageOps.exif_transpose(im).convert("RGB"); im=ImageOps.grayscale(im); im=ImageEnhance.Contrast(im).enhance(1.8); im=im.filter(ImageFilter.SHARPEN)
    return normalize_ocr_text(pytesseract.image_to_string(im,config="--psm 6"))
def normalize_ocr_text(t):
    return re.sub(r"\n{3,}","\n\n",re.sub(r"[ \t]+"," ",str(t).replace("\r","\n"))).strip()
def vals(t):
    pats={"sodium_mg":r"sodium\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*mg","added_sugar_g":r"added\s+sugars?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g","sugar_g":r"(?:total\s+)?sugars?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g","sat_fat_g":r"saturated\s+fat\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g","fiber_g":r"(?:dietary\s+)?fiber\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g","protein_g":r"protein\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g","energy_kcal":r"(?:energy|calories?)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:kcal|cal)"}
    return {k:float(m.group(1)) for k,p in pats.items() if (m:=re.search(p,t,re.I))}
def analyze_label(text):
    text=normalize_ocr_text(text); low=text.lower(); v=vals(text); als=[]; flags=[]; nf=[]
    for name,terms in ALLERGENS.items():
        for term in terms:
            if re.search(r"\b"+re.escape(term)+r"\b",low): als.append({"name":name,"match":term}); break
    reasons={"added sugar":"Can contribute added sweetness and energy.","refined oil":"Processed fat/oil signal; quantity and overall diet matter.","intense sweetener":"Intense sweetener signal; individual tolerance varies.","preservative/additive signal":"Preservative/additive keyword detected; consider the full label context."}
    for label,terms in RULES.items():
        for term in terms:
            if re.search(r"\b"+re.escape(term)+r"\b",low): flags.append({"ingredient":term,"reason":reasons[label]}); break
    if v.get("sodium_mg",0)>=400: nf.append({"nutrient":"Sodium","message":f'{v["sodium_mg"]:.0f} mg per listed serving triggers the configured review threshold.'})
    if v.get("added_sugar_g",0)>=10: nf.append({"nutrient":"Added sugars","message":f'{v["added_sugar_g"]:.1f} g per listed serving triggers the configured review threshold.'})
    elif v.get("sugar_g",0)>=15: nf.append({"nutrient":"Sugars","message":f'{v["sugar_g"]:.1f} g per listed serving triggers the configured review threshold.'})
    if v.get("sat_fat_g",0)>=5: nf.append({"nutrient":"Saturated fat","message":f'{v["sat_fat_g"]:.1f} g per listed serving triggers the configured review threshold.'})
    if "fiber_g" in v and v["fiber_g"]<2: nf.append({"nutrient":"Fiber","message":f'{v["fiber_g"]:.1f} g per listed serving is a low-fiber signal in this prototype.'})
    n=len(als)+len(flags)+len(nf); profile="Multiple review signals" if n>=5 else "Several review signals" if n>=3 else "Some review signals" if n else "No configured signals"
    summary=[]
    if als: summary.append("Potential allergen keywords were detected. Verify the package allergen statement.")
    if nf: summary.append("Some nutrition values crossed configured review thresholds; compare serving size and overall diet.")
    if flags: summary.append("Some ingredient keywords were flagged for closer label review.")
    if not summary: summary.append("No configured review signals were detected. This does not mean the product is universally healthy or suitable for everyone.")
    summary.append("Always compare results with the original package label because OCR and keyword matching can miss information.")
    audit=[["Nutrition extraction",k,x,"Regex-based local extraction"] for k,x in v]
    audit += [["Ingredient rule",x["ingredient"],"Triggered",x["reason"]] for x in flags]
    audit += [["Allergen rule",x["name"],x["match"],"Keyword match; not confirmation"] for x in als]
    audit += [["Nutrition rule",x["nutrient"],"Triggered",x["message"]] for x in nf]
    return {"profile":profile,"confidence":"Higher" if len(v)>=3 and len(text)>=100 else "Moderate" if len(text)>=50 else "Low","nutrition_values":v,"ingredient_flags":flags,"allergen_signals":als,"nutrition_flags":nf,"summary":summary,"audit":audit,"ocr_text":text}
