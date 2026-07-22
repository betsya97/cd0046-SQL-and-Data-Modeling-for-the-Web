from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # missing fields & relationships for Venue:
    genres = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean,default=False)
    seeking_description = db.Column(db.String(500))
class Artist(db.Model):
  __tablename__ = 'Artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  genres = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))

    #missing fields & relationships for Artist
  website = db.Column(db.String(500))
  seeking_venue = db.Column(db.Boolean,default=False)
  seeking_description = db.Column(db.String(500))
    

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
   __tablename__ = 'Show'
   id = db.Column(db.Integer, primary_key=True)
   start_time = db.Column(db.DateTime, nullable=False)
   
   #foreign keys and relationships
   venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
   artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
   
   venue = db.relationship('Venue',backref=db.backref('shows', lazy=True))
   artist = db.relationship('Artist',backref=db.backref('shows', lazy=True))