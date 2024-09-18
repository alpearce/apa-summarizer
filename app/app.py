from flask import Flask, abort, request, redirect, url_for, send_from_directory, render_template, jsonify
from app import ai_summarizer, parse_pdf
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PARSED_PDF_CACHE'] = 'parsed'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

system_prompt = "You are an animal shelter assistant that summarizes case files to improve animal care, and so the animals can be placed in adoptive homes. Tone should be honest but positive. Most entries in the files are dated, and summaries should highlight progress or changes over time."

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def upload_form():
    # Maybe add a way to select an already-uploaded file?
    return render_template('alt_upload.html', default_prompt=system_prompt)

@app.route('/summarize', methods=['POST'])
def summarize_file():
    system_prompt = request.form.get('prompt')
    name = request.form.get('animal-name')
    method = request.form.get('method')  # TODO: use

    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        abort(400, description="No file selected")
    
    if file and allowed_file(file.filename):
        filename = file.filename
        content = file.read()

        try:
            ai = ai_summarizer.AISummarizer("gpt-4o-mini", system_prompt)
        except Exception as e:
            abort(500, description=f"Failed to initialize AI summarizer: {e.message}")

        try:
            sections = parse_pdf.extract_sections_by_horizontal_lines(content)
        except Exception as e:
            abort(500, description=f"Error parsing PDF: {e.message}")

        # Summarize individual sections
        try:
            summaries = ai.summarize_file_in_sections(sections, "prompt", name)
        except Exception as e:
            abort(500, description=f"Error summarizing sections: {e.message}")

        # Handle titles
        titles_summarized = ', '.join(list(summaries.keys()))
        titles_ignored = ', '.join([item for item in list(sections.keys()) if item not in titles_summarized])

        # Summarize the summaries
        try:
            summary_doc = parse_pdf.document_from_sections(summaries)
            file_summary = ai.summarize_file(summary_doc, name)
        except Exception as e:
            abort(500, description=f"Error summarizing document: {e.message}")

        return render_template('summaries.html', file_name=filename, dog_name=name, file_summary=file_summary, summaries=summaries, titles_summarized=titles_summarized, titles_ignored=titles_ignored)

    else:
        abort(400, "Invalid file") 

@app.errorhandler(400)
def bad_request_error(error):
    return render_template('400.html', error_details=str(error)), 400

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html', error_details=str(error)), 500


# Start the server
if __name__ == '__main__':
    app.run(debug=True)