from flask import Flask, render_template
import tours_dao

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

@app.route("/") #route for the home page
def home():
    return render_template('home.html')
@app.route("/tours") #route for the tours page
def tours():
    db_tours = tours_dao.get_tours()
    sample_tours = [dict(row) for row in db_tours]
    return render_template("tour.html", tours=sample_tours)
    
if __name__ == '__main__':
    app.run(debug=True, port=5001)