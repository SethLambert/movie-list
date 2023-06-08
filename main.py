from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, FloatField, IntegerField
from wtforms.validators import DataRequired, NumberRange, URL
import requests
from dotenv import load_dotenv
import os

env_path = os.path.join('H:/repos/movie-list/','keys.env')
load_dotenv(env_path)

#CONSTANTS
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_API_KEY = os.getenv('TMDB_API_KEY')
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

#declare app
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

#declare database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new-books-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()
db.init_app(app)

#define classes
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)
    description = db.Column(db.Text, unique=False, nullable=False)
    rating = db.Column(db.Float, unique=False, nullable=True)
    ranking = db.Column(db.Integer, unique=False, nullable=True)
    review = db.Column(db.Text, unique=False, nullable=True)
    img_url = db.Column(db.String(250), unique=False, nullable=False)
    

    def __repr__(self):
        return f'<Movie {self.title}>'
    
class RateMovieForm(FlaskForm):
    id = HiddenField('id')
    title = HiddenField('Title', validators=[DataRequired()])
    year = HiddenField('Year', validators=[DataRequired()])
    description = HiddenField('Description', validators=[DataRequired()])
    rating = FloatField('Rating', validators=[NumberRange(0,10)])
    ranking = IntegerField('Ranking', validators=[])
    review = StringField('Review', validators=[])
    img_url = HiddenField('Movie Poster URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Update Rating')
    
class AddMovieForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=1900)])
    description = StringField('Description', validators=[DataRequired()])
    rating = FloatField('Rating', validators=[DataRequired(), NumberRange(0,10)])
    ranking = IntegerField('Ranking', validators=[DataRequired()])
    review = StringField('Review', validators=[DataRequired()])
    img_url = StringField('Movie Poster URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Add Movie')
    
class SearchMovieForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    submit = SubmitField('Search')
    
#declare variables
with app.app_context():
    all_movies = db.session.query(Movie).order_by(Movie.ranking).all()

#define functions
def refresh_movies():
    global all_movies
    with app.app_context():
        all_movies = db.session.query(Movie).order_by(Movie.ranking).all()
        #print(all_movies)

# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )

# with app.app_context():
#     db.create_all()
#     db.session.add(new_movie)
#     db.session.commit()

@app.route("/")
def home():
    refresh_movies()
    return render_template("index.html", movies=all_movies)

@app.route("/add", methods=['GET','POST'])
def add():
    form = AddMovieForm()        
    
    if form.validate_on_submit():
        #print("True")
        with app.app_context():
            movie = Movie(
                title = request.form["title"],
                year = request.form["year"],
                description = request.form["description"],
                rating = request.form["rating"],
                ranking = request.form["ranking"],
                review = request.form["review"],
                img_url = request.form["img_url"]
            )
            db.session.add(movie)
            db.session.commit()  
        refresh_movies()
        return render_template("index.html", movies=all_movies)     
    return render_template("add.html", form=form)

@app.route("/edit/<int:id>", methods=['GET','POST'])
def edit(id):
    with app.app_context():
        movie = Movie.query.get(id)
    form = RateMovieForm()        
    form.id.data = movie.id
    form.title.data = movie.title
    form.year.data = movie.year
    form.description.data = movie.description
    form.rating.data = movie.rating
    form.ranking.data = movie.ranking
    form.review.data = movie.review
    form.img_url.data = movie.img_url
    
    if form.validate_on_submit():
        #print("True")
        with app.app_context():
            movie = Movie.query.get(id)
            movie.title = request.form["title"]
            movie.year = request.form["year"]
            movie.description = request.form["description"]
            movie.rating = request.form["rating"]
            movie.ranking = request.form["ranking"]
            movie.review = request.form["review"]
            movie.img_url = request.form["img_url"]
            db.session.commit()  
        refresh_movies()
        return render_template("index.html", movies=all_movies)     
    return render_template("edit.html", movie=movie, form=form)

@app.route("/delete/<int:id>")
def delete(id):
    #print(id)
    #lookup book
    with app.app_context():
        movie = Movie.query.get(id)
        
    with app.app_context():
        db.session.delete(movie)
        db.session.commit()
        
    refresh_movies()
    return render_template("index.html", movies=all_movies)       

@app.route("/search", methods=['GET','POST'])
def search():
    form = SearchMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        headers = {
            "accept": "application/json",
            "Authorization": MOVIE_DB_API_KEY
        }
        response = requests.get(MOVIE_DB_SEARCH_URL, headers=headers, params={"query": movie_title})
        print(response)
        movies = response.json()["results"]
        #print(movies)
        return render_template("select.html", options=movies)  
    
    return render_template("search.html", form=form)

@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        headers = {
            "accept": "application/json",
            "Authorization": MOVIE_DB_API_KEY
        }
        response = requests.get(movie_api_url, headers=headers)
        print(response)
        data = response.json()
        #print(data)
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"],
            rating = 0,
            ranking = 99999,
            review = "No review"          
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True)
