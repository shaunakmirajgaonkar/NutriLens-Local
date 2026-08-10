from pathlib import Path
import json
import pandas as pd
import streamlit as st
from PIL import Image
from nutrition_engine import analyze_label, ocr_image

st.set_page_config(page_title="NutriLens Local", page_icon="🥗", layout="wide")

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#f4fbff,#f7fff9,#fffaf2);color:#17384d}
.block-container{max-width:1450px;padding:1.2rem 2rem 3rem}
section[data-testid="stSidebar"]{background:#eef8fb;border-right:1px solid #d9e9ee}
.hero{background:linear-gradient(120deg,#e9f7ff,#effff7,#fff8ed);border:1px solid #d6e7ed;border-radius:24px;padding:28px 32px;margin-bottom:18px}
.hero h1{color:#123b57;font-size:2.35rem;margin:0;font-weight:850}
.hero p{color:#536f7e;font-size:1.05rem;line-height:1.65}
.notice{background:#edf8ff;border:1px solid #cce5f2;border-left:6px solid #2386aa;border-radius:12px;padding:14px 17px;color:#214e66;margin-bottom:18px}
.warning{background:#fff7e9;border:1px solid #efd7a8;border-left:6px solid #d9952b;border-radius:12px;padding:14px 17px;color:#654a19;margin:12px 0}
.metric{background:#fff;border:1px solid #dce9ee;border-radius:16px;padding:16px;min-height:105px;box-shadow:0 3px 12px rgba(28,65,82,.05)}
.metric .label{color:#66808e;font-size:.77rem;font-weight:800;text-transform:uppercase;letter-spacing:.04em}
.metric .value{color:#153d58;font-size:1.35rem;font-weight:850;margin-top:7px;overflow-wrap:anywhere}
.stTextArea textarea,.stTextInput input{background:#fff!important;color:#17384d!important}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("## ⚙️ Reader Settings")
audit = st.sidebar.checkbox("Show ingredient audit trail", True)
ocr_out = st.sidebar.checkbox("Show extracted OCR text", True)
st.sidebar.markdown("---")
st.sidebar.caption("LOCAL NUTRITION LABEL INTELLIGENCE\nOCR and analysis run locally. No cloud vision/API is required.")

st.markdown("""<div class="hero"><h1>🥗 NutriLens Local</h1>
<p>Local-first packaged-food label reader that extracts label text from photos and explains ingredient, allergen, and nutrition signals in simple language.</p></div>""", unsafe_allow_html=True)
st.markdown("""<div class="notice"><b>Important:</b> Educational label-reading decision support only. It does not diagnose conditions, determine medical suitability, or guarantee allergen safety. Verify the original package label.</div>""", unsafe_allow_html=True)

tabs=st.tabs(["📷 Photo Reader","📝 Text Reader","📊 CSV Analysis","🧪 Demo","📚 Methodology"])

def show(r):
    cards=[("Profile",r["profile"]),("Ingredient flags",len(r["ingredient_flags"])),("Allergen signals",len(r["allergen_signals"])),("Nutrition flags",len(r["nutrition_flags"])),("Confidence",r["confidence"])]
    for c,(a,b) in zip(st.columns(5),cards):
        c.markdown(f'<div class="metric"><div class="label">{a}</div><div class="value">{b}</div></div>',unsafe_allow_html=True)
    if r["allergen_signals"]:
        st.subheader("⚠️ Potential allergen signals")
        for x in r["allergen_signals"]: st.markdown(f'- **{x["name"]}** — matched `{x["match"]}`')
        st.markdown('<div class="warning"><b>Verify:</b> keyword matching cannot confirm allergen presence or absence. Check the full package allergen statement.</div>',unsafe_allow_html=True)
    st.subheader("🧾 Ingredient insights")
    for x in r["ingredient_flags"]: st.markdown(f'- **{x["ingredient"]}** — {x["reason"]}')
    if not r["ingredient_flags"]: st.info("No configured ingredient signals detected.")
    st.subheader("📊 Nutrition insights")
    for x in r["nutrition_flags"]: st.markdown(f'- **{x["nutrient"]}** — {x["message"]}')
    if not r["nutrition_flags"]: st.info("No configured nutrition thresholds triggered.")
    st.subheader("💡 Simple-language summary")
    for x in r["summary"]: st.markdown(f"- {x}")
    if audit:
        with st.expander("🔍 Explainable audit trail"):
            st.dataframe(pd.DataFrame(r["audit"],columns=["Type","Signal","Value","Explanation"]),use_container_width=True,hide_index=True)
    if ocr_out and r.get("ocr_text"):
        with st.expander("🔤 Extracted text"):
            st.text_area("OCR",r["ocr_text"],height=220,label_visibility="collapsed")
    st.download_button("⬇️ Download JSON report",json.dumps(r,indent=2,ensure_ascii=False),"nutrilens_label_report.json","application/json")

with tabs[0]:
    st.subheader("📷 Read a packaged-food label photo")
    st.caption("Use a clear photo of the ingredients and nutrition panel.")
    f=st.file_uploader("Upload label image",type=["png","jpg","jpeg","webp"])
    if f:
        im=Image.open(f); st.image(im,caption="Uploaded label",width=650)
        if st.button("🔎 Extract and analyze label",type="primary"):
            try:
                with st.spinner("Running local OCR..."):
                    txt=ocr_image(im); r=analyze_label(txt); r["ocr_text"]=txt
                show(r)
            except Exception as e:
                st.error(str(e)); st.info("Use the Text Reader tab if local Tesseract is unavailable.")

with tabs[1]:
    st.subheader("📝 Analyze copied label text")
    txt=st.text_area("Ingredient list + nutrition panel",height=260,placeholder="Ingredients: whole wheat flour, sugar, palm oil, whey powder, soy lecithin...\nNutrition per serving: Energy 210 kcal, Saturated Fat 5 g, Sodium 420 mg, Total Sugars 14 g, Added Sugars 10 g, Fiber 2 g, Protein 4 g")
    if st.button("🧠 Analyze label text",type="primary"):
        if txt.strip(): show(analyze_label(txt))
        else: st.warning("Enter label text first.")

with tabs[2]:
    st.subheader("📊 CSV label analysis")
    st.caption("Required: label_text. Optional: product_id, product_name.")
    f=st.file_uploader("Upload food-label CSV",type=["csv"],key="csv")
    if f:
        df=pd.read_csv(f); st.dataframe(df,use_container_width=True,hide_index=True)
        if "label_text" not in df.columns: st.error("CSV must contain a label_text column.")
        elif st.button("📊 Analyze all labels",type="primary"):
            rows=[]
            for _,row in df.iterrows():
                r=analyze_label(row["label_text"])
                rows.append({"product_id":row.get("product_id",""),"product_name":row.get("product_name",""),"profile":r["profile"],"ingredient_flags":len(r["ingredient_flags"]),"allergen_signals":len(r["allergen_signals"]),"nutrition_flags":len(r["nutrition_flags"])})
            out=pd.DataFrame(rows); st.dataframe(out,use_container_width=True,hide_index=True)
            st.download_button("⬇️ Download analyzed CSV",out.to_csv(index=False),"NutriLens_Analyzed_Labels.csv","text/csv")

with tabs[3]:
    st.subheader("🧪 Synthetic demonstration dataset")
    d=pd.read_csv(Path(__file__).resolve().parent/"data"/"demo_food_labels.csv"); st.dataframe(d,use_container_width=True,hide_index=True)
    i=st.selectbox("Select product",range(len(d)),format_func=lambda x:f'{d.iloc[x]["product_id"]} — {d.iloc[x]["product_name"]}')
    if st.button("▶️ Analyze selected demo",type="primary"): show(analyze_label(d.iloc[i]["label_text"]))

with tabs[4]:
    st.subheader("📚 Methodology")
    st.markdown("""### Local OCR
Photos are read with Tesseract OCR through pytesseract when Tesseract is installed locally.

### Local analysis
The prototype uses transparent keyword and regex rules for common allergen signals, ingredient signals, and nutrition values.

### Safety
It is not a clinical nutrition model and cannot determine whether food is healthy or medically suitable for a specific person. OCR may misread text. Always verify the original package label.""")

