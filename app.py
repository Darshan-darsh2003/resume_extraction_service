from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2 as pdf
import google.generativeai as genai
import os
import wandb
from loguru import logger
from dotenv import load_dotenv
import json
from .dummyData import Dummy

app = Flask(__name__)
CORS(app)

load_dotenv()

# Configure WandB for logging (optional)
# wandb.login()


@app.route("/upload", methods=["POST"])
def upload_resume():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file.filename.endswith(".pdf"):
        try:
            text = extract_pdf_text(file)
            response = get_gemini_response(text)
            return jsonify(response)
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            return (
                jsonify({"error": "An error occurred while processing the request"}),
                500,
            )
    else:
        return jsonify({"error": "Unsupported file format"}), 400


def extract_pdf_text(uploaded_file):
    text = ""
    reader = pdf.PdfReader(uploaded_file)
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text


def get_gemini_response(input_text):
    try:
        logger.info("Generating prompt for Gemini Pro model...")
        jd = "AI Researcher"  # Example job description

        input_prompt = Dummy.get_data(input_text, jd)
        # Configure Gemini API
        genai.configure(api_key=os.environ.get("API_KEY"))

        # Initialize Gemini Pro model
        model = genai.GenerativeModel("gemini-pro")

        # Generate content using Gemini Pro model
        response = model.generate_content(input_prompt)
        response_text = response.text.strip()
        valid_response = None
        try:
            logger.info(f"Generated response: {(response_text)}")
            valid_response = json.loads(response_text.strip())
            logger.info("valid response: ", f"{valid_response}")
        except json.JSONDecodeError as json_error:
            logger.error(f"Error parsing JSON response: {json_error}")
            # Handle the error appropriately, e.g., return an error response
            return {"error": "Failed to parse JSON response"}

        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            # Handle other unexpected errors
            return {"error": "Unexpected error occurred"}

        # Example parsing of Gemini API response
        jd_match = "80%"  # Placeholder, parse response to get actual values
        missing_keywords = ["Python", "Machine Learning"]  # Placeholder
        profile_summary = "Experienced AI Researcher"  # Placeholder

        # Construct structured JSON response
        structured_response = {
            "JD Match": jd_match,
            "MissingKeywords": missing_keywords,
            "Profile Summary": profile_summary,
            "Resume Data": valid_response,
        }

        return structured_response

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return {"error": "An error occurred while processing the request"}


if __name__ == "__main__":
    app.run(debug=True, port=5002)
