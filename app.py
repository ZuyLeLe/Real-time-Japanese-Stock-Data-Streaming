from flask import request, render_template, jsonify, Flask
from pymongo import MongoClient
import plotly.graph_objects as go
import plotly.io as pio
import json

app = Flask(__name__, template_folder='templates')

uri = "mongodb+srv://Zuylele:LeAnhHuyen134@stock-data.kkn7o.mongodb.net/"
# MongoDB connection setup
client = MongoClient(uri)  # Replace with your MongoDB connection string if needed
db_3month = client['stock_3month']
db_5day = client['stock_5day']

@app.route('/')
def index():
    try:
        with open("Japan-ticker.json", 'r', encoding="utf-8") as f:
            stock_dict = json.load(f)
    except FileNotFoundError:
        return "Ticker file not found", 404
    except json.JSONDecodeError:
        return "Error decoding JSON", 500

    return render_template('index.html', sd=stock_dict)

@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    try:
        ticker = request.form['ticker']
        date_range = request.form['date_range']

        if not ticker or not date_range:
            return jsonify({'error': 'No ticker or date range provided'}), 400

        if date_range == '5d':
            collection = db_5day['historical_data']
        else:
            collection = db_3month['historical_data']

        # Fetch data from MongoDB
        stock_info = list(collection.find({'ticker': ticker}))

        if not stock_info:
            return jsonify({'error': 'No data found for the ticker'}), 404

        # Debugging print statement
        print("hi")
        if date_range == '5d':
            dates = [record['Datetime'] for record in stock_info]
        else:
            dates = [record['Date'] for record in stock_info]
        close_prices = [record['Close'] for record in stock_info]
        volumes = [record['Volume'] for record in stock_info]

        fig = go.Figure()

        
        
        fig.update_xaxes(rangebreaks=[{'pattern': 'day of week', 'bounds': [6, 1]}])

        fig.add_trace(go.Scatter(
            x=dates, 
            y=close_prices, 
            mode='lines', 
            name='Close Price', 
            line=dict(color='#1f77b4', width=2.5),
            connectgaps=True  
        ))

        fig.add_trace(go.Bar(
            x=dates, 
            y=volumes, 
            name='Volume', 
            marker=dict(color='rgba(50, 171, 96, 0.7)'),  
            yaxis='y2'
        ))

        fig.update_layout(
            title=f'Stock Price and Volume for {ticker}',
            title_font=dict(size=20, color='#333'),
            xaxis=dict(
                title='Date',
                title_font=dict(size=16, color='#333'),
                tickfont=dict(size=12),
                showgrid=True,
                gridcolor='rgba(200, 200, 200, 0.5)',
            ),
            yaxis=dict(
                title='Close Price',
                title_font=dict(size=16, color='#333'),
                tickfont=dict(size=12),
                showgrid=True,
                gridcolor='rgba(200, 200, 200, 0.5)',
                zerolinecolor='rgba(200, 200, 200, 0.5)',
            ),
            yaxis2=dict(
                title='Volume',
                title_font=dict(size=16, color='#333'),
                tickfont=dict(size=12),
                overlaying='y',
                side='right',
                showgrid=False,
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                bgcolor='rgba(255, 255, 255, 0.5)',
                bordercolor='#ccc',
                borderwidth=1,
            ),
            hovermode='x unified',
            plot_bgcolor='rgba(250, 250, 250, 1)',
            margin=dict(l=40, r=40, t=80, b=40)
        )

        graph_html = pio.to_html(fig, full_html=False)

        return jsonify({'graph_html': graph_html})
    except Exception as e:
        # Print the error to the console for debugging
        print(f"Error occurred: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
