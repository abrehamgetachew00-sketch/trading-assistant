import os
import base64
import io
from PIL import Image
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import markdown

load_dotenv()

app = Flask(__name__)

# Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class TradingAssistant:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
    def analyze_chart(self, image_path):
        """Analyze trading chart screenshot and provide trading recommendations"""
        
        # Load and process image
        img = Image.open(image_path)
        
        # System prompt for trading analysis
        prompt = """
        You are an expert technical analyst for trading. Analyze this chart screenshot and provide:
        
        1. CURRENT TREND: (Bullish/Bearish/Neutral)
        2. KEY LEVELS: Support and Resistance levels
        3. PATTERN RECOGNITION: Any chart patterns (Head & Shoulders, Double Top/Bottom, Flags, etc.)
        4. TECHNICAL INDICATORS (if visible): RSI, MACD, Moving Averages
        5. ACTIONABLE RECOMMENDATION: 
           - BUY at what price level with stop loss
           - SELL at what price level with stop loss
           - Or HOLD with reasoning
        6. RISK ASSESSMENT: High/Medium/Low with explanation
        7. CONFIDENCE SCORE: (0-100%)
        
        Be specific with price levels if visible. Provide conservative, risk-aware advice.
        """
        
        response = self.model.generate_content([prompt, img])
        return response.text
    
    def validate_recommendation(self, analysis_text):
        """Extract structured recommendations from analysis"""
        return {
            "raw_analysis": analysis_text,
            "formatted": markdown.markdown(analysis_text)
        }

assistant = TradingAssistant()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'chart_image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400
        
        file = request.files['chart_image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save temporary file
        temp_path = "temp_chart.png"
        file.save(temp_path)
        
        # Analyze chart
        analysis = assistant.analyze_chart(temp_path)
        structured = assistant.validate_recommendation(analysis)
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'analysis': structured['raw_analysis'],
            'formatted_analysis': structured['formatted']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
