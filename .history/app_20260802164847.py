#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime #added to bring functionality
from models import db, Venue, Artist, Show # import models / datatables
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
#app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://aaguilar:@localhost:5432/FyyurApp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev' #in order to CRUD

#db = SQLAlchemy(app)
db.init_app(app)              # <-- bind database models to this app
migrate = Migrate(app,db)

#----------------------------------------------------------------------------#
# Models. (see models.py)
#----------------------------------------------------------------------------#
   
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  venues = Venue.query.all()
  areas={}
  for venue in venues:
    key= (venue.city, venue.state)
    if key not in areas:
      areas[key] = []
    
    #counter for upcoming shows
    upcoming_shows = Show.query.filter(
      Show.venue_id == venue.id, 
      Show.start_time >= datetime.now()
    ).count()
    
    areas[key].append({
      "id":venue.id,
      "name":venue.name,
      "num_upcoming_shows":upcoming_shows
    })  
  
  # reference the tuple rather than the dictionary
  data=[]
  for (city,state), venues_list in areas.items():
    data.append({
      "city": city,
      "state": state,
      "venues": venues_list
    })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # search for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term=request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  data=[]
  for venue in venues:
    data.append({
      "id":venue.id, 
      "name":venue.name
    })
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get_or_404(venue_id)
  
  #lookup each artist buy joining Artist table to show and then filter by venue id
  past_shows = db.session.query(Show, Artist).join(
    Artist, Show.artist_id == Artist.id
    ).filter(
      Show.venue_id == venue_id, 
      Show.start_time < datetime.now()
      ).all()
  

  #future shows
  upcoming_shows = db.session.query(Show, Artist).join(
    Artist, Show.artist_id == Artist.id
    ).filter(
      Show.venue_id == venue_id, 
      Show.start_time >= datetime.now()
      ).all()

  past_shows_data=[]
  for show, artist in past_shows:
    #access artist data
    past_shows_data.append({ #append to create a list
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    })
  upcoming_shows_data=[]
  for show, artist in upcoming_shows:
    upcoming_shows_data.append({
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    })  
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(',') if venue.genres else [], 
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows_data,
    "upcoming_shows": upcoming_shows_data,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm(request.form)
  
  # runs validators in forms.py
  # if validation fails, re-render the form instead of going to the database
  if not form.validate_on_submit():
    flash('Please fix the errors in the form.')
    return render_template('forms/new_venue.html', form=form)
  
  try:
    venue = Venue(
      name=request.form['name'],
      city=request.form['city'],
      state=request.form['state'],
      address=request.form['address'],
      phone=request.form['phone'],
      #concat the string values into a list
      genres=",".join(request.form.getlist('genres')),
      image_link=request.form['image_link'],
      facebook_link=request.form['facebook_link'],
      website=request.form['website_link'], 
      seeking_talent=bool(request.form.get('seeking_talent')),
      seeking_description=request.form.get('seeking_description')
    )
    db.session.add(venue)
    db.session.commit()  
  # on successful db insert, flash success
    flash(f"Venue {request.form.get('name')} was successfully listed!")
  # TODO: on unsuccessful db insert, flash an error instead.
  except:
    db.session.rollback()
    error=True
    flash(f"Error occurred. Venue {request.form.get('name')} could not be listed.")
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue=Venue.query.get(venue_id)
    if not venue: #if venue doesn't exist, throw an error
      return {"error": "Venue not found"}, 404
    db.session.delete(venue)
    db.session.commit()
    return {"Venue successfully deleted": True}, 200
  except:
    db.session.rollback()
    db.session.close()
    error=True
    return {"error": "Can't delete venue"}, 500
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html') # go back to home after deleting, update show_venue.html for button

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()
  data=[]
  for artist in artists:
    data.append({"id":artist.id, "name":artist.name})
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term=request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  data = []
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })
  response={
    "count": len(data), #length of artist list gives the count
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  
  artist = Artist.query.get_or_404(artist_id)
  
  #join query to join show to Venue to get past show data and venue data in one single query 
  past_shows = db.session.query(Show, Venue).join(
    Venue, Show.venue_id == Venue.id
  ).filter(
    Show.artist_id == artist_id,
    Show.start_time < datetime.now()
  ).all() 

  #future shows
  upcoming_shows = db.session.query(Show, Venue).join(
      Venue, Show.venue_id == Venue.id
    ).filter(
      Show.artist_id == artist_id,
      Show.start_time >= datetime.now()
    ).all()

  past_shows_data=[]
  for show, venue in past_shows:
    #access venue data
    past_shows_data.append({ #append to create a list
      "venue_id": show.venue_id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    })
  upcoming_shows_data=[]
  for show, venue in upcoming_shows:
    upcoming_shows_data.append({
      "venue_id": show.venue_id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    })  
  
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(',') if artist.genres else [],
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows_data,
    "upcoming_shows": upcoming_shows_data,
    "past_shows_count": len(past_shows_data),
    "upcoming_shows_count": len(upcoming_shows_data),
  }
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # TODO: populate form with fields from artist with ID <artist_id>
  artist = Artist.query.get_or_404(artist_id)
  form = ArtistForm(obj=artist)
  form.genres.data = artist.genres.split(',') if artist.genres else []
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.get_or_404(artist_id)
  try:
    artist.name=request.form['name']
    artist.city=request.form['city']
    artist.state=request.form['state']
    artist.phone=request.form['phone']
    artist.genres=",".join(request.form.getlist('genres'))
    artist.image_link=request.form['image_link']
    artist.facebook_link=request.form['facebook_link']
    artist.website=request.form['website_link']
    artist.seeking_venue=bool(request.form.get('seeking_venue'))
    artist.seeking_description=request.form.get('seeking_description')
    
    db.session.commit()  
    flash(f"Artist {request.form.get('name')} was successfully updated!")
  except:
    db.session.rollback()
    error=True
    flash(f"Error occurred. Artist {request.form.get('name')} could not be updated.")
    
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm(obj=venue)
  form.genres.data = venue.genres.split(',') if venue.genres else []
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get_or_404(venue_id)
  try:
    venue.name=request.form['name']
    venue.city=request.form['city']
    venue.state=request.form['state']
    venue.address=request.form['address']
    venue.phone=request.form['phone']
      #concat the string values into a list
    venue.genres=",".join(request.form.getlist('genres'))
    venue.image_link=request.form['image_link']
    venue.facebook_link=request.form['facebook_link']
    venue.website=request.form['website_link']
    venue.seeking_talent=bool(request.form.get('seeking_talent'))
    venue.seeking_description=request.form.get('seeking_description')
   
    db.session.commit()  
    flash(f"Venue {venue.name} was successfully updated!")
  except Exception as e:
    db.session.rollback()
    error=True
    flash(f"Error occurred. Venue {venue.name} could not be updated.")
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    artist = Artist(
      name=request.form['name'],
      city=request.form['city'],
      state=request.form['state'],
      phone=request.form['phone'],
      #concat the string values into a list like in create_venue_submission
      genres=",".join(request.form.getlist('genres')),
      image_link=request.form['image_link'],
      facebook_link=request.form['facebook_link'],
      website=request.form['website_link'], 
      seeking_venue=bool(request.form.get('seeking_venue')),
      seeking_description=request.form.get('seeking_description')
    )
    db.session.add(artist)
    db.session.commit()  
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  except Exception as e:
    db.session.rollback()
    print(e)
    flash(f"Error occurred. Artist {request.form.get('name')} could not be listed.")
  
  finally:
    db.session.close()
    
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------


@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  
  shows = Show.query.all()
  
  results = db.session.query(Show, Venue, Artist).join(Venue, Show.venue_id == Venue.id).join(Artist, Show.artist_id == Artist.id).all()
      
  data=[]
  for show, venue, artist in results:
    data.append({
      "venue_id":show.venue_id, #from relationship in Show model
      "venue_name":venue.name, #from venue model
      "artist_id":show.artist_id, #from relationship in Show model
      "artist_name":artist.name, #from artist model
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    artist_id = request.form.get('artist_id','').strip()
    venue_id = request.form.get('venue_id','').strip()
    start_time=request.form.get('start_time', '').strip()
    
    show = Show(
      artist_id = int(artist_id),
      venue_id = int(venue_id),
      start_time=datetime.strptime(request.form.get('start_time'), '%Y-%m-%d %H:%M:%S')
    )
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  except Exception as e:
    db.session.rollback()
    print(e) # e.g., flash('An error occurred. Show could not be listed.')
    flash('An error occurred. Show could not be listed.')
 
  finally: #best practice
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=True) #auto reload page

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
