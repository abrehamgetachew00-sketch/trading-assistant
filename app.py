import os
import base64
import io
from PIL import Image
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import markdown
import re

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
        
        # System prompt for trading analysis with explicit buy/sell decision
        prompt = """
        You are an expert technical analyst. Analyze this chart and provide a CLEAR TRADING DECISION.
        
        YOU MUST CHOOSE ONE AND ONLY ONE OF THESE ACTIONS:
        🟢 BUY - If the chart shows bullish signals
        🔴 SELL - If the chart shows bearish signals  
        ⚪ HOLD/WAIT - If the market is indecisive or unclear
        
        FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
        
        ========================================
        🎯 TRADING DECISION: [BUY/SELL/HOLD]
        ========================================
        
        CONFIDENCE: [0-100]%
        
        📊 ENTRY LEVEL: [price or "Not visible"]
        🛑 STOP LOSS: [price or "Not visible"]
        🎯 TAKE PROFIT: [price or "Not visible"]
        
        📈 REASONS TO [BUY/SELL/HOLD]:
        • Reason 1
        • Reason 2
        • Reason 3
        
        ⚠️ RISK LEVEL: [HIGH/MEDIUM/LOW]
        
        💡 ADDITIONAL INSIGHTS:
        • Support: [levels]
        • Resistance: [levels]
        • Pattern: [pattern name if visible]
        
        BE DECISIVE. No wishy-washy language. Give a clear actionable signal.
        """
        
        response = self.model.generate_content([prompt, img])
        return response.text
    
    def extract_decision(self, analysis_text):
        """Extract the explicit trading decision from analysis"""
        
        # Look for BUY/SELL/HOLD in the text
        decision = "HOLD"  # default
        if "TRADING DECISION: BUY" in analysis_text or "DECISION: BUY" in analysis_text:
            decision = "BUY"
        elif "TRADING DECISION: SELL" in analysis_text or "DECISION: SELL" in analysis_text:
            decision = "SELL"
        elif "TRADING DECISION: HOLD" in analysis_text or "DECISION: HOLD" in analysis_text:
            decision = "HOLD"
            
        # Also check for emoji indicators
        if "🟢" in analysis_text and "BUY" in analysis_text.upper():
            decision = "BUY"
        elif "🔴" in analysis_text and "SELL" in analysis_text.upper():
            decision = "SELL"
        elif "⚪" in analysis_text and "HOLD" in analysis_text.upper():
            decision = "HOLD"
            
        # Extract confidence score
        confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', analysis_text)
        confidence = confidence_match.group(1) if confidence_match else "N/A"
        
        return {
            "decision": decision,
            "confidence": confidence,
            "full_analysis": analysis_text,
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
        structured = assistant.extract_decision(analysis)
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'decision': structured['decision'],
            'confidence': structured['confidence'],
            'analysis': structured['full_analysis'],
            'formatted_analysis': structured['formatted']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
