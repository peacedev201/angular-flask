import os
from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug import secure_filename
import uuid
import json
from flask_login import UserMixin
from datetime import datetime, timedelta
import time
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
import main
from main import db
from sqlalchemy_utils import Choice, ChoiceType, ImproperlyConfigured
from sqlalchemy_utils.types.choice import Enum


organizations = db.Table('organizations',
                         db.Column('organization_id', db.Integer, db.ForeignKey(
                             'organization.id'), primary_key=True),
                         db.Column('contributor_id', db.Integer, db.ForeignKey(
                             'contributor.id'), primary_key=True),
                         )


def current_milli_time(): return int(round(time.time() * 1000))


class UpdateStatus(Enum):
    pendding = 1
    declined = 2
    approved = 3

    @classmethod
    def convert_status_from_key(cls, value):
        if value == UpdateStatus.pendding:
            return 'pendding'
        elif value == UpdateStatus.declined:
            return 'declined'
        elif value == UpdateStatus.approved:
            return 'approved'
        return 'unknown'


class Contributor(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,  nullable=False)
    name = db.Column(db.String(255),  nullable=False)
    branchOfGov = db.Column(db.String(255))
    organizations = db.relationship(
        'Organization', secondary=organizations, lazy='subquery', backref=db.backref('contributors', lazy=True))
    ministry = db.Column(db.String(255))
    position = db.Column(db.String(255))
    gender = db.Column(db.String(255))
    age = db.Column(db.String(255))
    ancestry = db.Column(db.String(255))
    ethnicity = db.Column(db.String(255))
    imageurl = db.Column(db.String(255))
    adminuser_id = db.Column(
        db.Integer, db.ForeignKey('adminuser.id'))
    adminuser = db.relationship('Adminuser')

    updatedtime = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    status = db.Column(ChoiceType(UpdateStatus, impl=db.Integer()))

    def __init__(self, name, branchOfGov, ministry, position, gender, age, ancestry, ethnicity, imageurl, admin, status=UpdateStatus.pendding, user_id=None):
        self.name = name
        self.branchOfGov = branchOfGov
        self.ministry = ministry
        self.position = position
        self.gender = gender
        self.age = age
        self.ancestry = ancestry
        self.ethnicity = ethnicity
        self.imageurl = imageurl
        self.status = status
        self.adminuser = admin
        if not user_id:
            self.user_id = current_milli_time()
        else:
            self.user_id = user_id

    def __repr__(self):
        return '<Contributor %r>' % (self.name)

    @property
    def serialize(self):
        return {
            'postid': self.id,
            'userid': self.user_id,
            'name': self.name,
            'branchOfGov': self.branchOfGov,
            'organizations': [org.json()['name'] for org in self.organizations],
            'ministry': self.ministry,
            'position': self.position,
            'gender': self.gender,
            'age': self.age,
            'ancestry': self.ancestry,
            'ethnicity': self.ethnicity,
            'imageurl': self.imageurl,
            'status':  UpdateStatus.convert_status_from_key(self.status),
            'editor': self.adminuser.name,
            'updatedtime': self.updatedtime,
        }

    def json(self):
        return {
            'postid': self.id,
            'name': self.name,
            'branchOfGov': self.branchOfGov,
            'orgslist': [org.json() for org in self.organizations],
            'ministry': self.ministry,
            'position': self.position,
            'gender': self.gender,
            'age': self.age,
            'ancestry': self.ancestry,
            'ethnicity': self.ethnicity,
            'imageurl': self.imageurl,
        }

    def update_org_list(self, upOrgIds):

        oldOrgIds = [str(org.id) for org in self.organizations]
        orgIds = [str(upOrg) for upOrg in upOrgIds]
        removeItems = list(set(oldOrgIds) - set(orgIds))
        insertItems = list(set(orgIds) - set(oldOrgIds))
        for reItem in removeItems:
            selectedorg = Organization.find_org_by_id(int(reItem))
            self.organizations.remove(selectedorg)
        db.session.commit()

        for inItem in insertItems:
            selectedorg = Organization.find_org_by_id(int(inItem))
            self.organizations.append(selectedorg)

        db.session.commit()

    @classmethod
    def find_user_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_user_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def update_image_by_id(cls, user_id, filename):
        try:
            contributor = Contributor.find_user_by_id(user_id)
            contributor.imageurl = url_for(
                'static', filename="photos/" + filename)
            db.session.commit()
            return True
        except Exception as ex:
            return False

    @classmethod
    def delete_by_id(cls, _id):
        try:
            row = cls.query.filter_by(id=_id).first()
            print(row)
            db.session.delete(row)
            db.session.commit()
            return True
        except Exception as ex:
            return False

    @classmethod
    def find_all_contributors(cls):
        return cls.query.all()

    @classmethod
    def update_userdata(cls, _id, form):
        contributor = cls.query.filter_by(id=_id).first()
        try:
            f = form.file.data
            filename = uid.uuid4().hex + f.filename.split('.')[-1]
            print(filename)
            if filename:
                f.save(os.path.join('/static',
                                    'photos',  filename))
                contributor.imageurl = url_for(
                    'static', filename="photos/" + filename)
        except Exception as ex:
            print('not upload file')
            pass

        print(form.data)
        contributor.name = form.data.get('name')
        contributor.gender = form.data.get('gender')
        contributor.branchOfGov = form.data.get('branchOfGov')
        contributor.ministry = form.data.get('ministry')
        contributor.position = form.data.get('position')
        contributor.age = form.data.get('age')
        contributor.ancestry = form.data.get('ancestry')
        contributor.ethnicity = form.data.get('ethnicity')
        db.session.commit()

        orgIDs = form.data.get('orgslist'),
        contributor.update_org_list(orgIDs[0].split(','))

    @classmethod
    def update_userdata_by_json(cls, _id, editor, data):
        if editor.role == UserRole.admin:
            try:
                prevContibs = cls.query.filter_by(
                    user_id=data['userid']).filter_by(
                    status=UserRole.admin).first()
                if prevContibs and prevContibs.id != _id:
                    db.session.remove(prevContibs)
            except Exception as ex:
                pass

            contributor = cls.query.filter_by(id=_id).first()
            contributor.name = data['name']
            contributor.gender = data['gender']
            contributor.branchOfGov = data['branchOfGov']
            contributor.ministry = data['ministry']
            contributor.position = data['position']
            contributor.age = data['age']
            contributor.ancestry = data['ancestry']
            contributor.ethnicity = data['ethnicity']
            contributor.adminuser = editor
            contributor.status = UpdateStatus.approved
            db.session.commit()
            orgIDs = data['organizations']
            contributor.update_org_list(orgIDs)
        else:
            org_user = cls.query.filter_by(id=_id).first()
            contributor = cls.query.filter_by(
                user_id=org_user.user_id).filter_by(adminuser=editor).first()
            if not contributor:
                contributor = Contributor(
                    imageurl=org_user.imageurl,
                    name=org_user.name,
                    gender=org_user.gender,
                    branchOfGov=org_user.branchOfGov,
                    ministry=org_user.ministry,
                    position=org_user.position,
                    age=org_user.age,
                    ancestry=org_user.ancestry,
                    ethnicity=org_user.ethnicity,
                    admin=editor,
                    status=UpdateStatus.pendding,
                    user_id=org_user.user_id
                )

                db.session.add(contributor)
                db.session.commit()

            contributor.name = data['name']
            contributor.gender = data['gender']
            contributor.branchOfGov = data['branchOfGov']
            contributor.ministry = data['ministry']
            contributor.position = data['position']
            contributor.age = data['age']
            contributor.ancestry = data['ancestry']
            contributor.ethnicity = data['ethnicity']
            db.session.commit()
            orgIDs = data['organizations']
            contributor.update_org_list(orgIDs)

    @classmethod
    def add_userdata_by_json(cls, editor, data):
        contributor = Contributor(
            imageurl=url_for('static', filename="photos/default_avatar.png"),
            name=data['name'],
            gender=data['gender'],
            branchOfGov=data['branchOfGov'],
            ministry=data['ministry'],
            position=data['position'],
            age=data['age'],
            ancestry=data['ancestry'],
            ethnicity=data['ethnicity'],
            admin=editor,
            status=UpdateStatus.approved if editor.role and editor.role == UserRole.admin else UpdateStatus.pendding
        )
        db.session.add(contributor)
        db.session.commit()
        orgIDs = data['organizations']
        contributor.update_org_list(orgIDs)
        return contributor

    # @classmethod
    # def add_new_contributor(cls, form):
    #     f = form.file.data
    #     filename = secure_filename(f.filename)
    #     if not filename:
    #         flash('Error: Image file isn\'t exist')
    #         return

    #     from main import APP_ROOTPATH
    #     path = os.path.join(APP_ROOTPATH, 'static',
    #                         'photos',  filename)
    #     f.save(path)
    #     contributor = Contributor(
    #         imageurl=url_for('static', filename="photos/" + filename),
    #         name=form.data.get('name'),
    #         gender=form.data.get('gender'),
    #         branchOfGov=form.data.get('branchOfGov'),
    #         ministry=form.data.get('ministry'),
    #         position=form.data.get('position'),
    #         age=form.data.get('age'),
    #         ancestry=form.data.get('ancestry'),
    #         ethnicity=form.data.get('ethnicity')
    #     )
    #     db.session.add(contributor)
    #     db.session.commit()
    #     orgIDs = form.data.get('orgslist'),
    #     contributor.update_org_list(orgIDs[0].split(','))


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255),  nullable=False, unique=True)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }

    def json(self):
        return {
            'id': self.id,
            'name': self.name
        }

    @classmethod
    def find_org_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_org_by_name(cls, _name):
        return cls.query.filter_by(name=_name).first()

    @classmethod
    def find_all_organizes(cls):
        return cls.query.all()

    @classmethod
    def add_new_organize(cls, value):
        try:
            org = Organization.find_org_by_name(value)
            if org.name:
                return False
        except Exception as ex:
            pass
        org = Organization()
        org.name = value
        db.session.add(org)
        db.session.commit()
        return True

    @classmethod
    def update_by_id(cls, org_id, value):
        org = Organization.find_org_by_id(org_id)
        org.name = value
        db.session.commit()
        return True

    @classmethod
    def delete_by_id(cls, org_id):
        org = Organization.find_org_by_id(org_id)
        db.session.delete(org)
        db.session.commit()
        return True


class UserRole(Enum):
    admin = 1
    editor = 2
    contributer = 3
    notallowed = 5


class Adminuser(UserMixin, db.Model):
    # primary keys are required by SQLAlchemy
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    role = db.Column(ChoiceType(UserRole, impl=db.Integer()))

    @staticmethod
    def get_user_role_str(role):
        if(role == UserRole.admin):
            return 'admin'
        elif(role == UserRole.editor):
            return 'editor'
        return 'notallowed'

    @property
    def serialize(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': Adminuser.get_user_role_str(self.role),
        }

    def json(self):
        return {
            'email': self.email,
            'name': self.name,
            'role': Adminuser.get_user_role_str(self.role),
        }

    def generate_token(self, user_id):
        """ Generates the access token"""

        try:
            # set up a payload with an expiration time
            payload = {
                'exp': datetime.utcnow() + timedelta(minutes=300),
                'iat': datetime.utcnow(),
                'sub': user_id
            }
            # create the byte string token using the payload and the SECRET key
            from main import current_app
            jwt_string = jwt.encode(
                payload,
                current_app.config.get('SECRET_KEY'),
                algorithm='HS256'
            )
            return jwt_string

        except Exception as e:
            # return an error in string format if an exception occurs
            return str(e)

    @classmethod
    def find_user_by_email(cls, _email):
        return cls.query.filter_by(email=_email).first()

    @classmethod
    def find_user_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def update_user_by_id(cls, _id, data):
        if cls.find_user_by_id(_id):
            print(_id)
            contributor = cls.query.filter_by(id=_id).first()
            contributor.name = data['name']
            contributor.email = data['email']
            if data['role'] == 'admin':
                contributor.role = UserRole.admin
            elif data['role'] == 'editor':
                contributor.role = UserRole.editor
            elif data['role'] == 'notallowed':
                contributor.role = UserRole.notallowed
            db.session.commit()
            return True
        return False

    @classmethod
    def delete_user_by_id(cls, _id):
        try:
            row = cls.query.filter_by(id=_id).first()
            db.session.delete(row)
            db.session.commit()
            return True
        except Exception as ex:
            return False

    @classmethod
    def add_adminuser(cls, data):
        try:
            editor = Adminuser.find_user_by_email(data['email'])
            if editor and editor.email:
                return False
        except Exception as ex:
            pass
        editor = Adminuser()
        editor.name = data['name']
        editor.email = data['email']
        editor.password = generate_password_hash(
            data['password'], method='sha256')
        editor.role = UserRole.notallowed

        db.session.add(editor)
        db.session.commit()
        return True

    @classmethod
    def find_all_adminusers(cls):
        return cls.query.all()

    @classmethod
    def update_password(cls, oldpwd, newpwd):
        auth_header = request.headers.environ['HTTP_AUTHORIZATION']
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''
        print('--------------------')
        print(request.headers)
        if auth_token:
            resp = Adminuser.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                contributor = Adminuser.query.filter_by(id=resp).first()
                if contributor.password_is_valid(oldpwd):
                    contributor.password = generate_password_hash(
                        newpwd, method='sha256')
                    db.session.commit()
                    return True

        return False

    @staticmethod
    def decode_auth_token(token):
        """Decodes the access token from the Authorization header."""
        try:
            from main import current_app
            # try to decode the token using our SECRET variable
            payload = jwt.decode(token, current_app.config.get('SECRET_KEY'))
            return payload['sub']
        except jwt.ExpiredSignatureError:
            # the token is expired, return an error string
            return "Expired token. Please login to get a new token"
        except jwt.InvalidTokenError:
            # the token is invalid, return an error string
            return "Invalid token. Please register or login"

    def password_is_valid(self, password):
        """
        Checks the password against it's hash to validates the contributor's password
        """
        return check_password_hash(self.password, password)
