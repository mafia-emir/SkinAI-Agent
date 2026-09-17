import streamlit as st
import requests
import numpy as np
from PIL import Image, ImageFilter

# ==================================================================
# 0. PAGE SETUP & STYLING
# ==================================================================
st.set_page_config(page_title="SkinAI Agent", page_icon="✨", layout="centered")
st.markdown(
    """<style>
    .main{background-color:#0d0f1d;color:white;}
    .stButton>button{background-color:#6366f1!important;color:white;font-weight:bold;width:100%;border-radius:8px;}
    .card{background-color:#161930;padding:12px;border-radius:8px;margin-bottom:8px;border:1px solid #23274a;}
    .tag{background-color:#2e1a47;padding:3px 8px;border-radius:4px;font-size:11px;color:#c084fc;font-weight:bold;}
    .ai-box{background-color:#0b2521;border:1px solid #10b981;padding:12px;border-radius:8px;margin-bottom:15px;}
    .note-box{background-color:#241a0b;border:1px solid #f59e0b;padding:10px;border-radius:8px;margin-bottom:15px;font-size:13px;}
    </style>""",
    unsafe_allow_html=True
)

# ==================================================================
# GROQ API KEY
# NOTE: Hardcoding a real key here means anyone who sees this file
# (GitHub, screenshots, sharing it with someone) can use your key and
# spend your quota. If this key was ever pasted somewhere public,
# rotate it at https://console.groq.com/keys.
# ==================================================================
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ==================================================================
# 1. UNIFIED LANGUAGE LIST (shared by scanner UI + chatbot)
# ==================================================================
LANG_KEYS = ["English (UK)", "Roman Urdu", "Urdu", "German (Deutsch)", "Hindi (हिन्दी)"]

# ---- Scanner / product-finder UI text ----
LANG = {
    "English (UK)": {
        "title": "✨ SkinAI Agent",
        "step1": "📸 Step 1: Scan Your Face",
        "btn_scan": "Scan Skin",
        "scanning": "Analysing skin tone, texture and redness from your photo...",
        "ai_match": "✅ AI Scan Estimate!",
        "ai_detect_msg": "Based on colour and texture analysis of your photo, indicators of <b>{}</b> were detected.",
        "ai_disclaimer": "⚠️ This is a rough visual estimate based on image colour/texture, not a medical diagnosis. Please confirm or change the concern below, and see a dermatologist for an accurate diagnosis.",
        "step2": "📋 Step 2: Confirm Skin Details & Budget",
        "lbl_concern": "Skin Concern",
        "lbl_texture": "Skin Texture",
        "lbl_city": "Select City",
        "lbl_budget": "Budget Limit (PKR)",
        "results_title": "🧴 Recommendations for {} ({} Texture)",
        "day_title": "### ☀️ Morning Routine (Day)",
        "night_title": "### 🌙 Night Routine",
        "no_prod": "No products found within budget of {} PKR. Try increasing the budget.",
        "expert_title": "### 🏥 Recommended Dermatologists & Salons in {}",
        "expert_note": "Note: These listings are illustrative examples. Please verify details and book directly before visiting.",
        "maps_header": "📍 Find Skincare Services Near You",
        "maps_link": "🔍 Open {} Clinics directly on Google Maps ↗",
        "chat_header": "💬 SkinAI Expert Chatbot",
        "chat_greeting": "I am SkinAI Expert! Ask me anything about skincare — in any language.",
        "chat_placeholder": "Type your question here...",
        "chat_thinking": "SkinAI is thinking...",
    },
    "Roman Urdu": {
        "title": "✨ SkinAI Agent",
        "step1": "📸 Step 1: Apna Face Scan Karein",
        "btn_scan": "Skin Scan Karein",
        "scanning": "Aapki photo ka rang, texture aur laali (redness) analyze ho raha hai...",
        "ai_match": "✅ AI Scan Estimate!",
        "ai_detect_msg": "Aapki photo ke color aur texture analysis ke mutabiq, <b>{}</b> ke indicators detect huay hain.",
        "ai_disclaimer": "⚠️ Ye sirf photo ke rang/texture par based ek mota-mota (rough) andaza hai, medical diagnosis nahi. Neeche apna concern confirm/change kar lein, aur sahi tashkhees ke liye dermatologist se zaroor milein.",
        "step2": "📋 Step 2: Skin Details Aur Budget Confirm Karein",
        "lbl_concern": "Skin Ka Masla (Concern)",
        "lbl_texture": "Skin Ka Texture",
        "lbl_city": "Apna Shehar Chunein",
        "lbl_budget": "Budget Limit (PKR)",
        "results_title": "🧴 Suggested Plan for {} (Texture: {})",
        "day_title": "### ☀️ Subha ki Routine (Day Plan)",
        "night_title": "### 🌙 Raat ki Routine (Night Plan)",
        "no_prod": "Is {} PKR budget mein koi product nahi mili. Budget barhayein.",
        "expert_title": "### 🏥 {} Mein Recommended Dermatologists Aur Salons",
        "expert_note": "Note: Ye list sirf misal (illustrative) hai. Jaane se pehle khud tasdiq aur booking kar lein.",
        "maps_header": "📍 Apne Nazdeek Skincare Services Dhoondein",
        "maps_link": "🔍 {} Clinics Google Maps Par Kholein ↗",
        "chat_header": "💬 SkinAI Expert Chatbot",
        "chat_greeting": "Main SkinAI Expert hoon! Skincare ke baare mein kuch bhi poochein — koi bhi zaban mein.",
        "chat_placeholder": "Apna sawal yahan type karein...",
        "chat_thinking": "SkinAI soch raha hai...",
    },
    "Urdu": {
        "title": "✨ اسکن اے آئی ایجنٹ",
        "step1": "📸 پہلا مرحلہ: اپنا چہرہ اسکین کریں",
        "btn_scan": "چہرہ اسکین کریں",
        "scanning": "آپ کی تصویر کے رنگ، بناوٹ اور سرخی کا معائنہ ہو رہا ہے...",
        "ai_match": "✅ اے آئی اسکین کا اندازہ!",
        "ai_detect_msg": "آپ کی تصویر کے رنگ اور بناوٹ کے تجزیے کی بنیاد پر <b>{}</b> کے آثار پائے گئے ہیں۔",
        "ai_disclaimer": "⚠️ یہ صرف تصویر کے رنگ/بناوٹ پر مبنی ایک عمومی اندازہ ہے، طبی تشخیص نہیں۔ نیچے اپنا مسئلہ تصدیق یا تبدیل کریں، اور درست تشخیص کے لیے ماہر امراض جلد سے ضرور رجوع کریں۔",
        "step2": "📋 دوسرا مرحلہ: تفصیلات اور بجٹ کی تصدیق کریں",
        "lbl_concern": "جلد کا مسئلہ",
        "lbl_texture": "جلد کی بناوٹ",
        "lbl_city": "شہر منتخب کریں",
        "lbl_budget": "بجٹ کی حد (PKR)",
        "results_title": "🧴 تجویز کردہ پروڈکٹس برائے {} (بناوٹ: {})",
        "day_title": "### ☀️ صبح کی روٹین",
        "night_title": "### 🌙 رات کی روٹین",
        "no_prod": "بجٹ {} PKR میں کوئی پروڈکٹ دستیاب نہیں۔ براہ کرم بجٹ بڑھائیں۔",
        "expert_title": "### 🏥 {} میں تجویز کردہ ماہرین اور سیلون",
        "expert_note": "نوٹ: یہ فہرست محض مثال کے طور پر ہے۔ جانے سے پہلے خود تصدیق اور بکنگ کر لیں۔",
        "maps_header": "📍 اپنے قریب سکن کیئر سروسز تلاش کریں",
        "maps_link": "🔍 {} کے کلینکس گوگل میپس پر دیکھیں ↗",
        "chat_header": "💬 SkinAI ماہر چیٹ بوٹ",
        "chat_greeting": "میں SkinAI Expert ہوں! جلد کی دیکھ بھال کے بارے میں کچھ بھی پوچھیں — کسی بھی زبان میں۔",
        "chat_placeholder": "اپنا سوال یہاں لکھیں...",
        "chat_thinking": "SkinAI سوچ رہا ہے...",
    },
    "German (Deutsch)": {
        "title": "✨ SkinAI Agent",
        "step1": "📸 Schritt 1: Gesicht scannen",
        "btn_scan": "Haut scannen",
        "scanning": "Analysiere Hautton, Textur und Rötung Ihres Fotos...",
        "ai_match": "✅ KI-Scan-Schätzung!",
        "ai_detect_msg": "Basierend auf der Farb- und Texturanalyse Ihres Fotos wurden Anzeichen von <b>{}</b> erkannt.",
        "ai_disclaimer": "⚠️ Dies ist eine grobe visuelle Schätzung basierend auf Bildfarbe/-textur, keine medizinische Diagnose. Bitte bestätigen oder ändern Sie das Problem unten und konsultieren Sie einen Dermatologen für eine genaue Diagnose.",
        "step2": "📋 Schritt 2: Hautdetails & Budget bestätigen",
        "lbl_concern": "Hautproblem",
        "lbl_texture": "Hautstruktur",
        "lbl_city": "Stadt wählen",
        "lbl_budget": "Budgetlimit (PKR)",
        "results_title": "🧴 Empfehlungen für {} (Struktur: {})",
        "day_title": "### ☀️ Morgenroutine (Tag)",
        "night_title": "### 🌙 Abendroutine (Nacht)",
        "no_prod": "Keine Produkte innerhalb des Budgets von {} PKR gefunden. Erhöhen Sie das Budget.",
        "expert_title": "### 🏥 Empfohlene Dermatologen & Salons in {}",
        "expert_note": "Hinweis: Diese Einträge sind Beispiele. Bitte vor dem Besuch selbst prüfen und buchen.",
        "maps_header": "📍 Finden Sie Hautpflege-Dienste in Ihrer Nähe",
        "maps_link": "🔍 {}-Kliniken direkt auf Google Maps öffnen ↗",
        "chat_header": "💬 SkinAI Experten-Chatbot",
        "chat_greeting": "Ich bin SkinAI Expert! Fragen Sie mich alles über Hautpflege — in jeder Sprache.",
        "chat_placeholder": "Geben Sie hier Ihre Frage ein...",
        "chat_thinking": "SkinAI denkt nach...",
    },
    "Hindi (हिन्दी)": {
        "title": "✨ स्किनएआई एजेंट",
        "step1": "📸 चरण 1: अपना चेहरा स्कैन करें",
        "btn_scan": "स्किन स्कैन करें",
        "scanning": "आपकी फोटो के रंग, बनावट और लालिमा का विश्लेषण हो रहा है...",
        "ai_match": "✅ एआई स्कैन अनुमान!",
        "ai_detect_msg": "आपकी फोटो के रंग और बनावट विश्लेषण के आधार पर <b>{}</b> के संकेत मिले हैं।",
        "ai_disclaimer": "⚠️ यह केवल फोटो के रंग/बनावट पर आधारित एक सामान्य अनुमान है, चिकित्सा निदान नहीं। कृपया नीचे अपनी समस्या की पुष्टि करें या बदलें, और सही निदान के लिए त्वचा विशेषज्ञ से अवश्य मिलें।",
        "step2": "📋 चरण 2: विवरण और बजट की पुष्टि करें",
        "lbl_concern": "त्वचा की समस्या",
        "lbl_texture": "त्वचा की बनावट",
        "lbl_city": "शहर चुनें",
        "lbl_budget": "बजट सीमा (PKR)",
        "results_title": "🧴 {} के लिए सुझाव (बनावट: {})",
        "day_title": "### ☀️ सुबह की रूटीन",
        "night_title": "### 🌙 रात की रूटीन",
        "no_prod": "{} PKR बजट में कोई उत्पाद नहीं मिला। कृपया बजट बढ़ाएं।",
        "expert_title": "### 🏥 {} में अनुशंसित त्वचा विशेषज्ञ और सैलून",
        "expert_note": "नोट: यह सूची केवल उदाहरण के लिए है। जाने से पहले स्वयं पुष्टि और बुकिंग करें।",
        "maps_header": "📍 अपने आस-पास स्किनकेयर सेवाएं खोजें",
        "maps_link": "🔍 {} क्लीनिक सीधे गूगल मैप्स पर खोलें ↗",
        "chat_header": "💬 स्किनएआई एक्सपर्ट चैटबॉट",
        "chat_greeting": "मैं SkinAI Expert हूं! स्किनकेयर के बारे में कुछ भी पूछें — किसी भी भाषा में।",
        "chat_placeholder": "अपना सवाल यहां टाइप करें...",
        "chat_thinking": "SkinAI सोच रहा है...",
    },
}

# ---- Chatbot system-prompt language instructions (same unified keys) ----
CHAT_LANG_INSTRUCTIONS = {
    "English (UK)": "Respond in British English.",
    "Roman Urdu": "Roman Urdu mein jawab dein (Urdu likha English letters mein).",
    "Urdu": "جواب اردو رسم الخط میں دیں۔ (Respond in Urdu script.)",
    "German (Deutsch)": "Antworten Sie auf Deutsch.",
    "Hindi (हिन्दी)": "हिंदी लिपि में उत्तर दें। (Respond in Hindi script.)",
}

# ==================================================================
# SIDEBAR — shared settings for the whole app
# ==================================================================
with st.sidebar:
    st.header("⚙️ Settings")
    MODEL_NAME = st.selectbox(
        "Chatbot Model",
        ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        index=0
    )
    st.markdown("---")
    selected_lang = st.radio("🌐 Language / زبان / Zaban", LANG_KEYS)

T = LANG[selected_lang]
st.title(T["title"])
st.markdown(
    "<p style='text-align:center; color:#8b949e;'>Personalized Skincare, Powered by AI</p>",
    unsafe_allow_html=True
)
st.markdown("---")

# ==================================================================
# 2. CANONICAL SKIN CONCERN & TEXTURE KEYS (language-independent)
# ==================================================================
CONCERN_KEYS = ["acne", "oily", "dry", "combination", "sensitive",
                "aging", "pigmentation", "dull", "pores", "redness"]

CONCERN_LABELS = {
    "English (UK)": {
        "acne": "Acne & Pimples", "oily": "Oily & Greasy Skin", "dry": "Dry & Dehydrated Skin",
        "combination": "Combination Skin", "sensitive": "Sensitive Skin & Redness",
        "aging": "Fine Lines & Ageing", "pigmentation": "Dark Spots & Pigmentation",
        "dull": "Dull & Uneven Skin Tone", "pores": "Large Pores", "redness": "Redness & Rosacea"
    },
    "Roman Urdu": {
        "acne": "Acne Aur Pimples", "oily": "Oily Aur Chikni Skin", "dry": "Khushk (Dry) Skin",
        "combination": "Combination Skin", "sensitive": "Sensitive Skin Aur Laali",
        "aging": "Jhurriyan Aur Aging", "pigmentation": "Dark Spots Aur Pigmentation",
        "dull": "Dull Aur Bedaagh Na Rang", "pores": "Bare Pores", "redness": "Laali (Redness)"
    },
    "Urdu": {
        "acne": "ایکنی اور پمپلز", "oily": "آئلی اور چکنی جلد", "dry": "خشک جلد",
        "combination": "مخلوط (Combination) جلد", "sensitive": "حساس جلد اور سرخی",
        "aging": "جھریاں اور عمر رسیدگی", "pigmentation": "سیاہ دھبے اور پگمنٹیشن",
        "dull": "غیر یکساں اور بے رونق جلد", "pores": "بڑے مسام", "redness": "سرخی (Redness)"
    },
    "German (Deutsch)": {
        "acne": "Akne & Pickel", "oily": "Ölige Haut", "dry": "Trockene Haut",
        "combination": "Mischhaut", "sensitive": "Empfindliche Haut & Rötung",
        "aging": "Feine Linien & Alterung", "pigmentation": "Dunkle Flecken & Pigmentierung",
        "dull": "Fahle, ungleichmäßige Haut", "pores": "Große Poren", "redness": "Rötung & Rosacea"
    },
    "Hindi (हिन्दी)": {
        "acne": "मुंहासे और दाने", "oily": "तैलीय त्वचा", "dry": "रूखी त्वचा",
        "combination": "मिश्रित त्वचा", "sensitive": "संवेदनशील त्वचा और लालिमा",
        "aging": "झुर्रियां और उम्र के प्रभाव", "pigmentation": "काले धब्बे और पिगमेंटेशन",
        "dull": "बेजान और असमान त्वचा टोन", "pores": "बड़े रोमछिद्र", "redness": "लालिमा और रोसेशिया"
    }
}

TEXTURE_KEYS = ["dry", "oily", "combination", "flaky", "smooth", "sensitive_patchy"]

TEXTURE_LABELS = {
    "English (UK)": {"dry": "Dry", "oily": "Oily", "combination": "Combination",
                      "flaky": "Flaky", "smooth": "Smooth", "sensitive_patchy": "Sensitive/Patchy"},
    "Roman Urdu": {"dry": "Khushk (Dry)", "oily": "Chikni (Oily)", "combination": "Combination",
                   "flaky": "Flaky", "smooth": "Naram (Smooth)", "sensitive_patchy": "Sensitive/Patchy"},
    "Urdu": {"dry": "خشک", "oily": "چکنی", "combination": "مخلوط",
             "flaky": "فلیکی", "smooth": "نرم", "sensitive_patchy": "حساس/دھبے دار"},
    "German (Deutsch)": {"dry": "Trocken", "oily": "Ölig", "combination": "Mischhaut",
                          "flaky": "Schuppig", "smooth": "Glatt", "sensitive_patchy": "Empfindlich/Fleckig"},
    "Hindi (हिन्दी)": {"dry": "रूखी", "oily": "तैलीय", "combination": "मिश्रित",
                        "flaky": "परतदार", "smooth": "मुलायम", "sensitive_patchy": "संवेदनशील/धब्बेदार"}
}

# ==================================================================
# 3. PRODUCTS DATABASE — 10 products (5 day + 5 night) per concern
# ==================================================================
PRODUCTS_DB = {
    "acne": [
        {"name": "Saeed Ghani Neem Face Wash", "price": 380, "time": "Day"},
        {"name": "Bioaqua Tea Tree Cleanser", "price": 650, "time": "Day"},
        {"name": "Organic Riders Salicylic Foam", "price": 1450, "time": "Day"},
        {"name": "Jenpharm Spectra Matte Sunscreen SPF50", "price": 1550, "time": "Day"},
        {"name": "Cetaphil Oily Skin Cleanser", "price": 2200, "time": "Day"},
        {"name": "Acne Clear Gel", "price": 350, "time": "Night"},
        {"name": "Vince Salicylic Acid Serum 2%", "price": 1280, "time": "Night"},
        {"name": "The Ordinary Niacinamide 10%", "price": 2900, "time": "Night"},
        {"name": "La Roche-Posay Effaclar Duo", "price": 5200, "time": "Night"},
        {"name": "Differin Adapalene Gel (Rx)", "price": 1100, "time": "Night"},
    ],
    "oily": [
        {"name": "Hemani Neem Face Wash", "price": 320, "time": "Day"},
        {"name": "Vince Oil-Control Toner", "price": 950, "time": "Day"},
        {"name": "Simple Oil Balancing Moisturizer", "price": 1650, "time": "Day"},
        {"name": "Neutrogena Oil-Free Sunscreen SPF30", "price": 2100, "time": "Day"},
        {"name": "Cetaphil Pro Oil Absorbing Moisturizer", "price": 3400, "time": "Day"},
        {"name": "Saeed Ghani Charcoal Wash", "price": 350, "time": "Night"},
        {"name": "Saffron Salicylic Gel", "price": 850, "time": "Night"},
        {"name": "The Ordinary Niacinamide + Zinc", "price": 2900, "time": "Night"},
        {"name": "Primary Resurfacing Serum", "price": 1700, "time": "Night"},
        {"name": "Clinique Anti-Blemish Solutions", "price": 6500, "time": "Night"},
    ],
    "dry": [
        {"name": "Ponds Hydrating Facial Foam", "price": 450, "time": "Day"},
        {"name": "Saeed Ghani Aloe Vera Cream", "price": 380, "time": "Day"},
        {"name": "Cetaphil Moisturizing Lotion", "price": 2600, "time": "Day"},
        {"name": "Organic Riders Hyaluronic Moisturizer", "price": 1600, "time": "Day"},
        {"name": "Nivea Soft Cream", "price": 750, "time": "Day"},
        {"name": "Vince Hyaluronic Acid Serum", "price": 1180, "time": "Night"},
        {"name": "Conatural Repair Night Cream", "price": 1950, "time": "Night"},
        {"name": "CeraVe Moisturizing Cream", "price": 3800, "time": "Night"},
        {"name": "The Ordinary Natural Moisturizing Factors", "price": 2800, "time": "Night"},
        {"name": "La Roche-Posay Lipikar Balm", "price": 4600, "time": "Night"},
    ],
    "combination": [
        {"name": "Garnier Micellar Water", "price": 750, "time": "Day"},
        {"name": "Simple Refreshing Facial Wash", "price": 700, "time": "Day"},
        {"name": "Neutrogena Hydro Boost Water Gel", "price": 3200, "time": "Day"},
        {"name": "Ponds Super Light Gel", "price": 480, "time": "Day"},
        {"name": "Dermive Balancing Lotion", "price": 1200, "time": "Day"},
        {"name": "Vince Multivitamin Serum", "price": 1350, "time": "Night"},
        {"name": "The Ordinary Buffet Serum", "price": 5200, "time": "Night"},
        {"name": "Conatural Rosehip Oil", "price": 1650, "time": "Night"},
        {"name": "Bioderma Sensibio Cream", "price": 4200, "time": "Night"},
        {"name": "Clinique Dramatically Different Lotion", "price": 6800, "time": "Night"},
    ],
    "sensitive": [
        {"name": "Cetaphil Gentle Skin Cleanser", "price": 2400, "time": "Day"},
        {"name": "Simple Kind To Skin Wash", "price": 700, "time": "Day"},
        {"name": "La Roche-Posay Toleriane Fluide", "price": 5100, "time": "Day"},
        {"name": "Eucerin Sensitive Moisturizer", "price": 4800, "time": "Day"},
        {"name": "Nivea Sensitive Cream", "price": 550, "time": "Day"},
        {"name": "Bioderma Sensibio H2O", "price": 3900, "time": "Night"},
        {"name": "Avene Tolerance Extreme Cream", "price": 6200, "time": "Night"},
        {"name": "Vaseline Healing Jelly", "price": 350, "time": "Night"},
        {"name": "The Ordinary Marula Oil", "price": 2400, "time": "Night"},
        {"name": "Conatural Chamomile Balm", "price": 1800, "time": "Night"},
    ],
    "aging": [
        {"name": "Olay Total Effects Day Cream", "price": 2100, "time": "Day"},
        {"name": "Ponds Age Miracle", "price": 1600, "time": "Day"},
        {"name": "Neutrogena Rapid Wrinkle SPF30", "price": 3800, "time": "Day"},
        {"name": "L'Oreal Revitalift Day Cream", "price": 2600, "time": "Day"},
        {"name": "Garnier Vitamin C Serum", "price": 950, "time": "Day"},
        {"name": "The Ordinary Retinol 0.5%", "price": 2200, "time": "Night"},
        {"name": "Vince Retinol Night Serum", "price": 1650, "time": "Night"},
        {"name": "Olay Regenerist Night Cream", "price": 3600, "time": "Night"},
        {"name": "L'Oreal Revitalift Night Cream", "price": 2400, "time": "Night"},
        {"name": "RoC Retinol Correxion", "price": 8500, "time": "Night"},
    ],
    "pigmentation": [
        {"name": "Garnier Vitamin C Serum", "price": 950, "time": "Day"},
        {"name": "Vince Niacinamide Brightening Serum", "price": 1450, "time": "Day"},
        {"name": "Neutrogena Bright Boost", "price": 4200, "time": "Day"},
        {"name": "Organic Riders Vitamin C Cream", "price": 1650, "time": "Day"},
        {"name": "The Body Shop Vitamin C Glow", "price": 3200, "time": "Day"},
        {"name": "The Ordinary Alpha Arbutin 2%", "price": 2800, "time": "Night"},
        {"name": "Vince Kojic Acid Serum", "price": 1580, "time": "Night"},
        {"name": "Murad Rapid Age Spot Serum", "price": 12500, "time": "Night"},
        {"name": "Saeed Ghani Papaya Cream", "price": 420, "time": "Night"},
        {"name": "Skinceuticals Discoloration Defense", "price": 21000, "time": "Night"},
    ],
    "dull": [
        {"name": "Ponds Bright Beauty Cream", "price": 480, "time": "Day"},
        {"name": "Garnier Bright Complete", "price": 550, "time": "Day"},
        {"name": "Vince Vitamin C + E Serum", "price": 1400, "time": "Day"},
        {"name": "Nivea Cellular Luminous Cream", "price": 2200, "time": "Day"},
        {"name": "Olay Luminous Tone Serum", "price": 2900, "time": "Day"},
        {"name": "The Ordinary Glycolic Acid 7% Toner", "price": 2600, "time": "Night"},
        {"name": "Vince AHA Exfoliating Serum", "price": 1350, "time": "Night"},
        {"name": "Pixi Glow Tonic", "price": 3400, "time": "Night"},
        {"name": "Saeed Ghani Turmeric Pack", "price": 350, "time": "Night"},
        {"name": "Kiehl's Midnight Recovery Concentrate", "price": 9800, "time": "Night"},
    ],
    "pores": [
        {"name": "Simple Pore Minimizing Wash", "price": 750, "time": "Day"},
        {"name": "Vince Niacinamide Pore Serum", "price": 1350, "time": "Day"},
        {"name": "The Ordinary Niacinamide 10% + Zinc", "price": 2900, "time": "Day"},
        {"name": "Neutrogena Pore Refining Toner", "price": 2100, "time": "Day"},
        {"name": "Garnier Pure Active Wash", "price": 500, "time": "Day"},
        {"name": "The Ordinary Salicylic Acid 2%", "price": 2800, "time": "Night"},
        {"name": "Vince BHA Exfoliating Toner", "price": 1180, "time": "Night"},
        {"name": "Paula's Choice Skin Perfecting 2% BHA", "price": 8500, "time": "Night"},
        {"name": "Clinique Pore Refining Solutions", "price": 6200, "time": "Night"},
        {"name": "Saeed Ghani Clay Mask", "price": 380, "time": "Night"},
    ],
    "redness": [
        {"name": "Avene Antirougeurs Day Cream", "price": 5800, "time": "Day"},
        {"name": "Eucerin Redness Relief Day Cream", "price": 4900, "time": "Day"},
        {"name": "La Roche-Posay Rosaliac Cream", "price": 5600, "time": "Day"},
        {"name": "Cetaphil Redness Relieving Moisturizer", "price": 3200, "time": "Day"},
        {"name": "Simple Soothing Facial Wash", "price": 700, "time": "Day"},
        {"name": "Avene Antirougeurs Night Cream", "price": 6400, "time": "Night"},
        {"name": "The Ordinary Azelaic Acid 10%", "price": 2600, "time": "Night"},
        {"name": "Vince Centella Calming Serum", "price": 1450, "time": "Night"},
        {"name": "Bioderma Sensibio Night Cream", "price": 4700, "time": "Night"},
        {"name": "Conatural Aloe Vera Gel", "price": 650, "time": "Night"},
    ],
}

# ==================================================================
# 4. EXPERTS DATABASE — dermatologists/salons per city
#    NOTE: Example/illustrative listings — verify independently before booking.
# ==================================================================
EXPERTS_DB = {
    "Lahore": [
        {"n": "Dr. Kazim Hussain Skin Clinic", "t": "Dermatologist — Acne & Laser"},
        {"n": "Skin Studio DHA", "t": "Cosmetic Skin Care"},
        {"n": "Dr. Ayesha Fareed Clinic", "t": "Dermatologist — Pigmentation"},
        {"n": "Glamour Beauty Salon Gulberg", "t": "Facials & Skin Treatments"},
        {"n": "Aesthetica Clinic", "t": "Anti-Ageing & Botox"},
    ],
    "Karachi": [
        {"n": "Dr. Zara Khan Skin Centre", "t": "Dermatologist — General Skin"},
        {"n": "The Skin Clinic DHA", "t": "Cosmetic Dermatology"},
        {"n": "Dr. Omar Saeed Clinic", "t": "Dermatologist — Acne Specialist"},
        {"n": "Sublime Beauty Lounge", "t": "Facials & Skin Care"},
        {"n": "Derma Care Clifton", "t": "Laser & Pigmentation Treatment"},
    ],
    "Islamabad": [
        {"n": "Dr. Naeem Butt Clinic (F-8)", "t": "Dermatologist — Acne & Eczema"},
        {"n": "Cosmo Aesthetic Centre", "t": "Skin Specialist — Anti-Ageing"},
        {"n": "Dr. Sana Malik Skin Clinic", "t": "Dermatologist — Pigmentation"},
        {"n": "Rejuvenate Beauty Clinic", "t": "Facials & Laser Treatments"},
        {"n": "Blue Area Skin Studio", "t": "Cosmetic Skin Care"},
    ],
    "Faisalabad": [
        {"n": "Dr. Muhammad Saleem Clinic", "t": "Dermatologist — General Skin"},
        {"n": "Amina Z Salon", "t": "Facials & Skin Care"},
        {"n": "Dr. Farah Iqbal Skin Centre", "t": "Dermatologist — Acne Specialist"},
        {"n": "Glow Up Beauty Lounge", "t": "Cosmetic Treatments"},
    ],
    "Multan": [
        {"n": "Dr. Asif Shah Clinic (Cantt)", "t": "Dermatologist — Pigmentation"},
        {"n": "Royal Aesthetic Care", "t": "Skin Care & Laser"},
        {"n": "Dr. Hina Riaz Skin Clinic", "t": "Dermatologist — General Skin"},
        {"n": "Elegance Beauty Salon", "t": "Facials & Skin Treatments"},
    ],
    "Gujrat": [
        {"n": "Dr. Jamil Ahmed Clinic", "t": "Dermatologist — General Skin"},
        {"n": "Glow Skin Clinic", "t": "Skin Specialist — Acne & Pigmentation"},
        {"n": "Radiance Beauty Salon", "t": "Facials & Skin Care"},
    ],
    "Bahawalpur": [
        {"n": "Dr. Tariq Mahmood Clinic", "t": "Dermatologist — General Skin"},
        {"n": "Rose Beauty Salon", "t": "Facials & Skin Care"},
        {"n": "Dr. Sadia Yousaf Skin Centre", "t": "Dermatologist — Acne Specialist"},
    ],
}

# ==================================================================
# 5. IMAGE-BASED SKIN ANALYSIS (heuristic, NOT random, NOT a medical diagnosis)
# ==================================================================
def analyze_skin_image(img: Image.Image):
    img_small = img.convert("RGB").resize((150, 150))
    arr = np.asarray(img_small).astype(float)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    brightness = float((r.mean() + g.mean() + b.mean()) / 3)
    redness = float(r.mean() - (g.mean() + b.mean()) / 2)

    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    saturation = float(((mx - mn) / (mx + 1e-5)).mean() * 255)

    gray = img_small.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    texture_score = float(np.asarray(edges).astype(float).std())

    gray_arr = np.asarray(gray).astype(float)
    step = 15
    patch_means = [
        gray_arr[i:i + step, j:j + step].mean()
        for i in range(0, 150, step) for j in range(0, 150, step)
    ]
    blemish_variance = float(np.std(patch_means))

    scores = {
        "redness": max(0.0, redness - 8) * 2.0,
        "dry": max(0.0, texture_score - 20) * 1.5 + max(0.0, 60 - saturation) * 0.5,
        "oily": max(0.0, saturation - 40) + max(0.0, brightness - 150) * 0.3,
        "acne": max(0.0, blemish_variance - 10) * 2.0,
        "dull": max(0.0, 90 - brightness) * 0.6 + max(0.0, 30 - saturation) * 0.4,
        "pigmentation": max(0.0, blemish_variance - 8) * 1.2 + max(0.0, 90 - brightness) * 0.3,
        "pores": max(0.0, texture_score - 15) * 1.0,
        "aging": max(0.0, texture_score - 25) * 0.8,
        "combination": 5.0,
    }
    scores["sensitive"] = scores["redness"] * 0.7

    top_concern = max(scores, key=scores.get)

    if saturation > 45 and brightness > 140:
        texture_guess = "oily"
    elif texture_score > 25:
        texture_guess = "flaky"
    elif redness > 15:
        texture_guess = "sensitive_patchy"
    elif saturation < 25:
        texture_guess = "dry"
    else:
        texture_guess = "smooth"

    return top_concern, texture_guess

# ==================================================================
# 6. GROQ CHATBOT HELPERS
# ==================================================================
def build_system_prompt(language_key):
    language_instruction = CHAT_LANG_INSTRUCTIONS[language_key]
    return f"""You are SkinAI Expert, a knowledgeable, friendly virtual dermatology and skincare assistant.

SCOPE:
- You ONLY discuss topics related to skin: skincare routines, acne, dryness, oily skin,
  pigmentation, anti-aging, skin conditions, dermatology, ingredients (like retinol,
  niacinamide, salicylic acid, etc.), sunscreen, product recommendations, and general
  skin health.
- If the user asks something unrelated to skin/skincare/dermatology, politely decline
  and say (in {language_key}) something like: "Sorry, I am a skin specialist assistant
  and can only help with skin-related topics." Do not answer the unrelated question.

STYLE:
- Give clear, accurate, well-organized, and genuinely helpful answers.
- Keep responses concise but complete (use short paragraphs or bullet points when useful).
- Always remind users that for serious or persistent skin issues, they should consult
  a real dermatologist in person.

LANGUAGE:
- {language_instruction}
"""

def query_groq_ai(user_message, language_key, api_key, model):
    if not api_key:
        return "⚠️ Please enter your Groq API key to start chatting."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": build_system_prompt(language_key)},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.6
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        res_json = response.json()
        return res_json["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError:
        try:
            err_detail = response.json().get("error", {}).get("message", "")
        except Exception:
            err_detail = ""
        return f"⚠️ Groq API error: {err_detail or response.status_code}. Check your API key/model."
    except requests.exceptions.RequestException:
        return "⚠️ Could not reach Groq right now. Please check your internet connection and try again."
    except (KeyError, IndexError):
        return "⚠️ Unexpected response from Groq. Please try again."

# ==================================================================
# 7. STEP 1 — FACE SCAN
# ==================================================================
st.subheader(T["step1"])
uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

if uploaded_file:
    photo = Image.open(uploaded_file)
    st.image(photo, width=230)
    if st.button(T["btn_scan"]):
        with st.spinner(T["scanning"]):
            concern_key, texture_key = analyze_skin_image(photo)
        st.session_state["ai_concern"] = concern_key
        st.session_state["ai_texture"] = texture_key

if "ai_concern" in st.session_state:
    display_label = CONCERN_LABELS[selected_lang][st.session_state["ai_concern"]]
    st.markdown(
        f"<div class='ai-box'><span style='color:#10b981;font-weight:bold;'>{T['ai_match']}</span><br>"
        f"{T['ai_detect_msg'].format(display_label)}</div>",
        unsafe_allow_html=True
    )
    st.markdown(f"<div class='note-box'>{T['ai_disclaimer']}</div>", unsafe_allow_html=True)

# ==================================================================
# 8. STEP 2 — CONCERN / TEXTURE / BUDGET
# ==================================================================
st.subheader(T["step2"])

default_concern_index = CONCERN_KEYS.index(st.session_state["ai_concern"]) if "ai_concern" in st.session_state else 0
default_texture_index = TEXTURE_KEYS.index(st.session_state["ai_texture"]) if "ai_texture" in st.session_state else 0

u_concern_key = st.selectbox(
    T["lbl_concern"], CONCERN_KEYS,
    index=default_concern_index,
    format_func=lambda k: CONCERN_LABELS[selected_lang][k]
)
u_texture_key = st.selectbox(
    T["lbl_texture"], TEXTURE_KEYS,
    index=default_texture_index,
    format_func=lambda k: TEXTURE_LABELS[selected_lang][k]
)

# ---- Single shared city selector (used for both Maps and Experts sections) ----
city = st.selectbox(T["lbl_city"], list(EXPERTS_DB.keys()))

budget_limit = st.slider(T["lbl_budget"], min_value=500, max_value=30000, value=5000, step=500)

# ==================================================================
# 9. STEP 3 — FILTER & DISPLAY PRODUCTS
# ==================================================================
st.write("---")
st.markdown(T["results_title"].format(
    CONCERN_LABELS[selected_lang][u_concern_key],
    TEXTURE_LABELS[selected_lang][u_texture_key]
))

filtered_prod = [p for p in PRODUCTS_DB[u_concern_key] if p["price"] <= budget_limit]
day_r = [p for p in filtered_prod if p["time"] == "Day"]
night_r = [p for p in filtered_prod if p["time"] == "Night"]

st.markdown(T["day_title"])
if day_r:
    for p in day_r:
        st.markdown(f"<div class='card'><b>{p['name']}</b> — <span class='tag'>PKR {p['price']}</span></div>", unsafe_allow_html=True)
else:
    st.info(T["no_prod"].format(budget_limit))

st.markdown(T["night_title"])
if night_r:
    for p in night_r:
        st.markdown(f"<div class='card'><b>{p['name']}</b> — <span class='tag'>PKR {p['price']}</span></div>", unsafe_allow_html=True)
else:
    st.info(T["no_prod"].format(budget_limit))

# ==================================================================
# 10. STEP 4 — MAPS EMBED (uses the same city selected above)
# ==================================================================
st.write("---")
st.header(T["maps_header"])

query_param = f"dermatologists+in+{city}"
map_embed_url = f"https://maps.google.com/maps?q={query_param}&t=&z=13&ie=UTF8&iwloc=&output=embed"
st.markdown(
    f'<iframe src="{map_embed_url}" width="100%" height="320" '
    f'style="border:0; border-radius:14px;" allowfullscreen loading="lazy"></iframe>',
    unsafe_allow_html=True
)
st.markdown(f"### [{T['maps_link'].format(city)}](https://www.google.com/maps/search/{query_param})")

# ==================================================================
# 11. STEP 5 — EXPERT / SALON LOCATOR (same city)
# ==================================================================
st.write("---")
st.markdown(T["expert_title"].format(city))
for exp in EXPERTS_DB[city]:
    maps_query = exp["n"].replace(" ", "+") + "+" + city
    st.markdown(
        f"<div class='card'><b>{exp['n']}</b> — <span style='color:#a78bfa;'>{exp['t']}</span><br>"
        f"<a href='https://www.google.com/maps/search/{maps_query}' target='_blank' "
        f"style='color:#6366f1;text-decoration:none;font-size:12px;'>View on Google Maps ↗</a></div>",
        unsafe_allow_html=True
    )
st.caption(T["expert_note"])

# ==================================================================
# 12. STEP 6 — CHATBOT (same language selector)
# ==================================================================
st.write("---")
st.header(T["chat_header"])

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [{"role": "assistant", "content": T["chat_greeting"]}]

for msg in st.session_state.chat_messages:
    st.chat_message(msg["role"]).write(msg["content"])

if user_query := st.chat_input(T["chat_placeholder"]):
    st.chat_message("user").write(user_query)
    st.session_state.chat_messages.append({"role": "user", "content": user_query})

    with st.spinner(T["chat_thinking"]):
        bot_reply = query_groq_ai(user_query, selected_lang, GROQ_API_KEY, MODEL_NAME)

    st.chat_message("assistant").write(bot_reply)
    st.session_state.chat_messages.append({"role": "assistant", "content": bot_reply})
