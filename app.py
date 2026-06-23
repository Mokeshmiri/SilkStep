from flask import Flask, render_template

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

@app.route("/") #route for the home page
def home():
    return render_template('home.html')
@app.route("/tours") #route for the tours page
def tours():
    sample_tours = [
        {
            "title": "Old Tehran Walking Tour",
            "schedule": "Sat & Sun at 10:00 AM",
            "duration": "4 hours",
            "summary": "Explore the historic heart of Tehran, from the 16th-century Shahreza Palace to the 13th-century Jameh Mosque.",
        },
        {
            "title": "Bazaar & Market Tour",
            "schedule": "Mon, Wed, Fri at 2:00 PM",
            "duration": "3 hours",
            "summary": "Discover the vibrant markets of Tehran, from the Grand Bazaar to the spice and textile souks.",
        },
        {
            "title": "Museum & Art Tour",
            "schedule": "Tue & Thu at 3:00 PM",
            "duration": "2 hours",
            "summary": "Visit the National Museum of Iran and explore the city's vibrant art scene.",
        },
    ]
    return render_template('tour.html', tours=sample_tours)

if __name__ == '__main__':
    app.run(debug=True)