from flask import Flask, render_template, request, send_file
from fpdf import FPDF
from bidi.algorithm import get_display
import arabic_reshaper
import pandas as pd
import io
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 🧪 قائمة التحاليل والرينجات الطبيعية
plus_range = "None / + / ++ / +++"
tests = {
    "BLOOD GROUP": "Depends on type",
    "E.S.R": "0-22mm/hr(M),0-29mm/hr(W)",
    "PT": "11-13.5 seconds",
    "PTT": "25-35 seconds",
    "I.N.R": "0.8-1.1",
    "FIBRINOGEN": "200-400 mg/dL",
    "T3": "80-200 ng/dL",
    "T4": "5.0-12.0 µg/dL",
    "TSH": "0.4-4.0 mIU/L",
    "FT4": "0.7-1.9 ng/dL",
    "FT3": "2.3-4.2 pg/mL",
    "H.PYLORI-Ab": "Negative",
    "C.R.P": "< 3.0 mg/L",
    "TYPHOID IGG": "Negative",
    "TYPHOID IGM": "Negative",
    "S.cholesterol": "< 200 mg/dL",
    "S.triglyceride": "< 150 mg/dL",
    "RBS": "70-140 mg/dL",
    "B.UREA": "7-20 mg/dL",
    "S.CREATININE": "0.6-1.3 mg/dL",
    "URIC ACID": "3.5-7.2 mg/dL",
    "S.Alk": "44-147 IU/L",
    "S.G.O.T": "5-40 U/L",
    "S.G.P.T": "7-56 U/L",
    "LH": "1.24-7.8 IU/L",
    "FSH": "1.5-12.4 IU/L",
    "AMH": "1.0-4.0 ng/mL",
    "S.TESTO": "300-1000 ng/dL",
    "P.R.L": "4.8-23.3 ng/mL",
    "Urea Test": "7-20 mg/dL",
    "PUS": plus_range,
    "R.B.C": "4.7-6.1 million cells/mcL",
    "EPTH. CELL": plus_range,
    "Cast": plus_range,
    "Ca Oxalate": plus_range,
    "A.URATE": plus_range,
    "A.PHOSPHATE": plus_range,
    "Uric acid": "3.5-7.2 mg/dL",
    "MUCUS": plus_range,
    "Bacteria": plus_range
}

# ✅ تحميل البيانات من Excel إذا كان موجودًا
data = []
if os.path.exists("lab_results.xlsx"):
    data = pd.read_excel("lab_results.xlsx").to_dict(orient='records')

def reshape(text):
    return get_display(arabic_reshaper.reshape(str(text)))

class LabPDF(FPDF):
    def __init__(self, patient):
        super().__init__()
        self.patient = patient
        self.add_font("Amiri", "", "Amiri-Regular.ttf", uni=True)
        self.set_font("Amiri", size=13)

    def header(self):
        try:
            self.image("static/logo.png", x=10, y=10, w=150)
        except:
            pass
        self.ln(40)
        self.set_font("Amiri", size=13)
        self.cell(0, 30, text=reshape("تقرير التحاليل المرضية"), ln=True, align='C')
        self.ln(5)
        self.set_font("Amiri", size=11)
        self.multi_cell(0, 40, text=reshape(
            f"الاسم: {self.patient['name']}   العمر: {self.patient['age']}   الهاتف: {self.patient['phone']}   التاريخ: {self.patient['date']}"
        )) 
        self.ln(5)
       
    def footer(self):
        self.set_y(-30)
        try:
            self.image("static/footer.jpg", x=10, w=self.w - 10)
        except:
            pass
        self.set_font("Amiri", size=10)
        self.set_text_color(100)
        self.set_y(-15)
        self.cell(0, 10, text=reshape(f"الصفحة {self.page_no()}"), align='C')

def generate_pdf(patient, results):
    pdf = LabPDF(patient)
    pdf.add_page()
    pdf.set_font("Amiri", size=11)

    col_width = 60
    line_height = 10
    margin_bottom = 30  # المسافة المحجوزة للتذييل

    def draw_table_header():
        pdf.set_fill_color(200, 220, 255)
        pdf.set_font("Amiri", size=11)
        pdf.cell(col_width, 10, reshape("التحليل"), border=1, align='C', fill=True)
        pdf.cell(col_width, 10, reshape("النتيجة"), border=1, align='C', fill=True)
        pdf.cell(col_width, 10, reshape("القيمة الطبيعية"), border=1, align='C', fill=True)
        pdf.ln()

    draw_table_header()

    for test, result in results.items():
        test_text = reshape(test)
        result_text = reshape(result)
        normal_text = reshape(tests[test])

        # حساب ارتفاع السطر
        def get_cell_height(text):
            temp = FPDF()
            temp.add_page()
            temp.add_font("Amiri", "", "Amiri-Regular.ttf", uni=True)
            temp.set_font("Amiri", size=11)
            temp.set_xy(0, 0)
            temp.multi_cell(col_width, line_height, text)
            return temp.get_y()

        h_test = get_cell_height(test_text)
        h_result = get_cell_height(result_text)
        h_normal = get_cell_height(normal_text)
        max_height = max(h_test, h_result, h_normal)

        # التحقق من المساحة المتبقية في الصفحة
        if pdf.get_y() + max_height + margin_bottom > pdf.h:
            pdf.add_page()
            draw_table_header()

        # رسم الخلايا الثلاثة
        x_start = pdf.get_x()
        y_start = pdf.get_y()

        for i, text in enumerate([test_text, result_text, normal_text]):
            x = x_start + i * col_width
            y = y_start
            pdf.set_xy(x, y)
            pdf.multi_cell(col_width, line_height, text, border=1, align='C')
            current_y = pdf.get_y()
            remaining = max_height - (current_y - y)
            if remaining > 0:
                pdf.set_xy(x, current_y)
                pdf.cell(col_width, remaining, '', border=1)

        pdf.set_y(y_start + max_height)

    # حفظ الملف في الذاكرة
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        patient = {
            'name': request.form['name'],
            'age': request.form['age'],
            'phone': request.form['phone'],
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        selected_tests = request.form.getlist('tests')
        return render_template('results.html', patient=patient, selected_tests=selected_tests, tests=tests)
    return render_template('index.html', tests=tests)

@app.route('/generate', methods=['POST'])
def generate():
    patient = {
        'name': request.form['name'],
        'age': request.form['age'],
        'phone': request.form['phone'],
        'date': request.form['date']
    }
    results = {key: request.form[key] for key in request.form if key not in ['name', 'age', 'phone', 'date']}
    record = {**patient, **results}
    data.append(record)
    df = pd.DataFrame(data)
    df.to_excel("lab_results.xlsx", index=False)
    pdf_buffer = generate_pdf(patient, results)
    filename = f"{patient['name']}_report.pdf"
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        name = request.form['search_name'].strip().lower()
        results_found = [d for d in data if d['name'].strip().lower() == name]
        if not results_found:
            return render_template('search.html', not_found=True)
        result = results_found[-1]
        return render_template('search.html', result=result)
    return render_template('search.html')

@app.route('/print_report', methods=['POST'])
def print_report():
    patient = {
        'name': request.form['name'],
        'age': request.form['age'],
        'phone': request.form['phone'],
        'date': request.form['date']
    }
    results = {key: request.form[key] for key in request.form if key not in ['name', 'age', 'phone', 'date']}
    pdf_buffer = generate_pdf(patient, results)
    filename = secure_filename(f"{patient['name']}_report.pdf")
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@app.route('/download', methods=['GET', 'POST'])
def download_excel():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '1985':
            file_path = "lab_results.xlsx"
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True)
            else:
                return "الملف غير موجود بعد. الرجاء إدخال بيانات أولاً.", 404
        else:
            return render_template('download.html', error=True)
    return render_template('download.html')

# ✅ تشغيل التطبيق باستخدام المنفذ الصحيح
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

