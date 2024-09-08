from flask import Flask, request, redirect, url_for, send_from_directory, render_template, jsonify
from app import ai_summarizer
from app import parse_pdf
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
    method = request.form.get('method') # TODO: use

    if 'file' not in request.files:
        return redirect(request.url) # TODO: idk what this is meant to be
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = file.filename
        # Save the file if we want to re-process it later.
        #file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        content = file.read()

        ai = ai_summarizer.AISummarizer("gpt-4o", system_prompt)
        sections = parse_pdf.extract_sections_by_horizontal_lines(content)
        # Summarize individual sections in more detail.
        summaries = ai.summarize_file_in_sections(sections, "prompt", name)
        titles_summarized = ', '.join(list(summaries.keys()))
        titles_ignored = ', '.join([item for item in list(sections.keys()) if item not in titles_summarized])
        # Summarize the summaries because why not.
        summary_doc = parse_pdf.document_from_sections(summaries)
        file_summary = ai.summarize_file(summary_doc, name)

        return render_template('summaries.html', file_name=filename, dog_name="Beluga", file_summary=file_summary, summaries=summaries, titles_summarized=titles_summarized, titles_ignored=titles_ignored)
        # TODO: include all the info, just testing the  json
        #return jsonify({'summary': file_summary}), 200
    else:
        return jsonify({'error': 'Invalid file'}), 400


@app.errorhandler(400)
def bad_request_error(error):
    # Add additional context here
    error_details = "There was an issue with your request. Please check the data and try again."
    return render_template('400.html', error_details=error_details), 400

@app.errorhandler(500)
def internal_server_error(error):
    # Add additional context here
    error_details = "An unexpected error occurred on our side. We are working to fix it."
    return render_template('500.html', error_details=error_details), 500

#@app.route('/process/<filename>')
#def process_file(filename):
#    prompt = request.args.get('prompt')
#    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#    if os.path.exists(file_path):
#        text = parse_pdf.extract_text_from_pdf(file_path)
#        # write the file to the parsed pdf cache so we can keep using it
#        ai = ai_summarizer.AISummarizer("gpt-4o")
#        summary = ai.summarize_text(text, prompt)
#        # offer a redirection to redo the prompt
#        return (f"Processed content of {filename}.<br>"
#                f"Prompt: {prompt}<br>"
#                f"Summary: {summary}")
#    else:
#        return "File not found."

# Start the server
if __name__ == '__main__':
    app.run(debug=True)