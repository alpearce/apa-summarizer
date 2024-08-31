from flask import Flask, request, redirect, url_for, send_from_directory, render_template, jsonify
import ai_summarizer
import os
import parse_pdf

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PARSED_PDF_CACHE'] = 'parsed'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

default_oneshot_prompt = "You will be provided with notes about a shelter dog. Summarize all the text relating to the dog's behavior, interactions with people, interactions with other animals, and its response to training, if applicable. There is a date above each entry. Make sure the summary reflects progression over time."

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def upload_form():
    # Maybe add a way to select an already-uploaded file?
    return render_template('upload.html', default_prompt=default_oneshot_prompt)

@app.route('/upload', methods=['POST'])
def upload_file():
    prompt = request.form.get('prompt')
    name = request.form.get('dog-name')

    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('process_file', filename=filename, name=name, prompt=prompt))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/process/<filename>/<name>/<prompt>')
def process_file(filename, name, prompt):
    ai = ai_summarizer.AISummarizer("gpt-4o")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        sections = parse_pdf.extract_sections_by_horizontal_lines(file_path)
        # Summarize individual sections in more detail.
        summaries = ai.summarize_file_in_sections(sections, "prompt", name)
        titles_summarized = ', '.join(list(summaries.keys()))
        titles_ignored = ', '.join([item for item in list(sections.keys()) if item not in titles_summarized])
        # Summarize the summaries because why not.
        summary_doc = parse_pdf.document_from_sections(summaries)
        file_summary = ai.summarize_file(summary_doc, name)

        return render_template('summaries.html', file_name=filename, dog_name="Beluga", file_summary=file_summary, summaries=summaries, titles_summarized=titles_summarized, titles_ignored=titles_ignored)
    else:
        return "File not found", 404


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