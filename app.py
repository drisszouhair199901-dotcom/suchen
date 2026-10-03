import re
import urllib.parse
import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st

# إعدادات الصفحة
st.set_page_config(
    page_title="مستخرج إيميلات التقديمات الألمانية 🤖", page_icon="🔍", layout="centered"
)

# عنوان الأداة والوصف
st.title("🔍 روبوت استخراج إيميلات التقديمات (Ausbildung Extractor)")
st.write(
    "حدد التخصص، التاريخ، والمنطقة لاستخراج إيميلات الشركات والمؤسسات الألمانية مباشرة!"
)

# ----------------- نموذج إدخال البيانات -----------------
st.subheader("⚙️ معايير البحث")

col1, col2 = st.columns(2)
with col1:
    domain = st.text_input("1. التخصص / الدومين (Fachbereich):", "Pflegefachmann")
    location = st.text_input("2. المدينة أو الولاية (Ort/Bundesland):", "NRW")

with col2:
    start_date = st.text_input("3. تاريخ البداية (Ausbildungsbeginn):", "2027")
    max_results = st.slider("4. عدد نتائج البحث للجمع:", 10, 50, 20)

# ----------------- منطق البحث والاستخراج -----------------


def search_google_emails(query, num_results):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
    }

    # صياغة الاستعلام للبحث المباشر عن الإيميلات المتعلقة بالتقديمات
    search_query = f'{query} "bewerbung" "@"'
    url = (
        f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(search_query)}"
    )

    extracted_emails = set()

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            snippets = soup.find_all("a", class_="result__snippet")

            # البحث عن صيغ الإيميلات داخل النصوص باستخدام Regex
            email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

            for snippet in snippets:
                text = snippet.get_text()
                matches = re.findall(email_pattern, text)
                for email in matches:
                    email_clean = email.lower().strip()
                    # استبعاد امتدادات الصور والتجهيزات الصوتية
                    if not email_clean.endswith(
                        (".png", ".jpg", ".jpeg", ".gif")
                    ):
                        extracted_emails.add(email_clean)

    except Exception as e:
        st.error(f"حدث خطأ أثناء البحث: {e}")

    return list(extracted_emails)


# ----------------- زر التشغيل وعرض النتائج -----------------
if st.button("🚀 بدء استخراج الإيميلات", type="primary"):
    full_query = f"Ausbildung {domain} {location} {start_date}"

    with st.spinner("جاري جلب واستخراج الإيميلات من الشبكة... ⏳"):
        emails = search_google_emails(full_query, max_results)

    if emails:
        st.success(f"🎉 تم العثور على {len(emails)} إيميل بنجاح!")

        # عرض النتائج في جدول
        df = pd.DataFrame(emails, columns=["البريد الإلكتروني (Email)"])
        st.dataframe(df, use_container_width=True)

        # تحويل القائمة لنص وقابلية النسخ/التحميل
        emails_text = "\n".join(emails)

        st.subheader("📋 القائمة جاهزة للنسخ المباشر لروبوت الإرسال:")
        st.text_area("انسخ الإيميلات من هنا:", value=emails_text, height=150)

        # زر تحميل ملف CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 تحميل القائمة بصيغة CSV",
            data=csv,
            file_name=f"emails_{domain}_{location}.csv",
            mime="text/csv",
        )
    else:
        st.warning(
            "لم يتم العثور على إيميلات مباشرة في هذه المحاولة، جرب تغيير كليمة البحث أو المنطقة."
        )
