from flask import Flask, render_template, request, jsonify
from ContentAnalyzer import ContentAnalyzer
from firebase_setup import init_firebase


app = Flask(__name__)

init_firebase()

@app.route('/')
def home():
    return render_template('index.html',  deneme="deneme")

@app.route('/run-python-code', methods=['GET'])
def run_python_code():
    url = request.args.get('url')  # Get the URL parameter from the request
    
    try:
        analyzer = ContentAnalyzer(url)
        result = analyzer.run()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    

if __name__ == '__main__':
    app.run(debug=True)

