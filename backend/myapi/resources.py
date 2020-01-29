import os
from functools import wraps
from flask import jsonify, Flask, request, url_for
from flask_restful import Resource, Api, reqparse
from flask_restful import fields, marshal_with, abort
from .models import Contributor, Organization
from werkzeug import secure_filename, check_password_hash
import pandas as pd
import json
import time


from flask.views import MethodView
from flask import Blueprint, make_response, request, jsonify
from myapi.models import Adminuser, UserRole, UpdateStatus


def current_milli_time(): return int(round(time.time() * 1000))

# Get user information from request Auth Header


def get_current_user(auth_header):
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token = ''

    if auth_token:
        resp = Adminuser.decode_auth_token(auth_token)
        if not isinstance(resp, str):
            user = Adminuser.query.filter_by(id=resp).first()
            return user
    return None


# Checking Authentication from request
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.environ['HTTP_AUTHORIZATION']
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''

        if auth_token:
            resp = Adminuser.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                user = Adminuser.query.filter_by(id=resp).first()

                return f(*args, **kwargs)
            return abort(401)
        else:
            return abort(401)
    return decorated

# Checking Admin Authentication from request


def admin_requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.environ['HTTP_AUTHORIZATION']
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''

        if auth_token:
            resp = Adminuser.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                contributor = Adminuser.query.filter_by(id=resp).first()
                # args['editor'] = contributor
                if contributor.role == UserRole.admin:
                    return f(*args, **kwargs)
            return abort(401)
        else:
            return abort(401)
    return decorated


# url: /api/admin
class AdminManage(Resource):
    # editor and admin update password
    @requires_auth
    def post(self):
        try:
            data = json.loads(request.data.decode())
            if data and data['old'] and data['new']:
                if Adminuser.update_password(data['old'], data['new']):
                    return {
                        "res": 'ok',
                    }, 201
            return {"res": 'failed'}, 200
        except Exception as ex:
            print(ex)
            return {
                'res': 'failed',
            }, 200

# url: /api/admin/users/


class AdminUserList(Resource):
    # get admin and editors list
    @admin_requires_auth
    def get(self):
        try:
            contributors = Adminuser.find_all_adminusers()
            json_list = [contributor.serialize for contributor in contributors]
            # return make_response(jsonify([contributor.json() for contributor in users])), 200
            print(json_list)
            return json_list, 200
        except Exception as ex:
            print(ex)
            return {
                'res': 'failed',
            }, 400

from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "testpeopledb@gmail.com",#"os.environ['EMAIL_USER'],
    "MAIL_PASSWORD": "Pa$$word123"#os.environ['EMAIL_PASSWORD']
}

app.config.update(mail_settings)
mail = Mail(app)


def send_mail(mail_address="", mail_context=""):
    with app.app_context():
        msg = Message(subject="Congratulation!",
                      sender=app.config.get("MAIL_USERNAME"),
                      recipients=[mail_address],  # replace with your email for testing
                      body="Your request was approved! Please login again.")
        mail.send(msg)
    return "success"
# url: /api/users/
class AdminUserManage(Resource):
    # updating editor and admin user
    @admin_requires_auth
    def post(self, user_id):
        try:
            data = json.loads(request.data.decode())
            if Adminuser.update_user_by_id(user_id, data):
                result = send_mail(mail_address=data['email'])
                return {
                    'res': result,

                }, 200
            else:
                return {
                    'res': 'No Contributor exist',
                }, 400
        except Exception as ex:
            print(ex)
            return {
                'res': 'failed',
            }, 400

    # deleting admin and editor
    @admin_requires_auth
    def delete(self, user_id):
        try:
            if Adminuser.delete_user_by_id(user_id):

                return 'ok', 200
            else:
                return {
                    'res': 'No Contributor exist',
                }, 400
        except Exception as ex:
            print(ex)
            return {
                'res': 'failed',
            }, 400

# url: /api/csv/
class CSVImports(Resource):

    def getOrganization(self, orgstr):
        orgs = orgstr.split(';')
        res = []
        for orgEle in orgs:
            print(orgEle)
            try:
                org = Organization.find_org_by_name(orgEle)
            except Exception as ex:
                pass

            if not org:
                Organization.add_new_organize(orgEle)
                org = Organization.find_org_by_name(orgEle)

            res.append(org.id)
        print(res)
        return res
    # add user data from csv
    @requires_auth
    def post(self):
        try:
            print('--- post start-------')
            csvFile = request.files['file']
            filename = secure_filename(csvFile.filename)
            if not filename:
                return {
                    'res': 'failed',
                    'msg': 'CSV file isn\'t exsit'
                }, 200
            filename = str(current_milli_time()) + '.csv'

            from main import APP_ROOTPATH
            path = os.path.join(APP_ROOTPATH, 'temp')
            if not os.path.exists(path):
                os.makedirs(path)

            path = os.path.join(APP_ROOTPATH, 'temp', filename)
            csvFile.save(path)
            data = pd.read_csv(path)
            print('---- add_userdata_by_json ---------')
            user = get_current_user(
                request.headers.environ['HTTP_AUTHORIZATION'])
            for row in range(0, len(data)):
                newPerson = {
                    'name': data['Person (ENG)'][row],
                    'branchOfGov': data['Branch of Government'][row],
                    'ministry': data['Ministry'][row],
                    'position': data['Position'][row],
                    'gender': data['Gender'][row],
                    'age': str(data['Age'][row]),
                    'ancestry': data['Ancestry'][row],
                    'ethnicity': data['Ethnicity'][row],
                    'organizations': self.getOrganization(data['Organization'][row]),
                }
                Contributor.add_userdata_by_json(user, newPerson)

            os.remove(path)
            return {
                'res': 'ok'
            }, 200
        except Exception as ex:
            print(ex)
            return {
                'res': 'failed',
                'msg': 'CSV file isn\'t exsit'
            }, 200

# url : /api/users/<string:user_id>
class UserDetails(Resource):

    def get_user_by_id(self, user_id):
        users = Contributor.query.filter_by(id=user_id).one()
        return jsonify(users.serialize)

# all users information
    def get(self, user_id):
        return self.get_user_by_id(user_id)
# update new user data
    @requires_auth
    def post(self, user_id):
        data = json.loads(request.data.decode())
        editor = get_current_user(
            request.headers.environ['HTTP_AUTHORIZATION'])
        if data:
            Contributor.update_userdata_by_json(user_id, editor, data)
            return 'ok', 201
        return 'failed', 200

    # for image upload
    @requires_auth
    def put(self, user_id):
        print('--- put start-------')
        image = request.files['image']
        filename = secure_filename(image.filename)
        if not filename:
            return {
                'res': 'failed',
                'msg': 'Image file isn\'t exsit'
            }, 200

        from main import APP_ROOTPATH
        path = os.path.join(APP_ROOTPATH, 'static',
                            'photos',  filename)
        image.save(path)
        if Contributor.update_image_by_id(user_id, filename):
            return {
                'res': 'ok'
            }, 200

        print('-----put end-----')

        return 'failed', 200
#  delete selected user.
    @requires_auth
    def delete(self, user_id):
        if Contributor.delete_by_id(user_id):
            return 'ok', 200
        else:
            return 'failed', 200

# url: /api/users
class UserLists(Resource):
    def get_users_serialize(self):
        users = Contributor.query.filter_by(status=UpdateStatus.approved).all()
        return jsonify([b.serialize for b in users])
# show all user data
    def get(self):
        return self.get_users_serialize()

# url: /api/admin/usersmanage
class UserManageLists(Resource):
    def get_users_serialize(self):
        users = Contributor.query.all()
        return jsonify([b.serialize for b in users])
    
    # admin side contributors
    @requires_auth
    def get(self):
        return self.get_users_serialize()
    
    # admin side contributors
    @requires_auth
    def post(self):
        data = json.loads(request.data.decode())
        user = get_current_user(request.headers.environ['HTTP_AUTHORIZATION'])
        
        if data:
            contributor = Contributor.add_userdata_by_json(user, data)
            if contributor:
                return {
                    "res": 'ok',
                    "postid": contributor.id
                }, 201
            else:
                return {
                    "res": 'failed',
                    "message": 'Entity already exists!'
                }, 201
        return {"res": 'failed'}, 200

# url: /api/orgs/<string:org_id>
class OrgDetails(Resource):

    def get_org_by_id(self, org_id):
        orgs = Organization.query.filter_by(id=org_id).one()
        return jsonify(orgs.serialize)

    def get(self, org_id):
        return self.get_org_by_id(org_id)

    @requires_auth
    def post(self, org_id):
        parser = reqparse.RequestParser()
        parser.add_argument('name')
        args = parser.parse_args()
        try:
            if args and args.name and Organization.update_by_id(org_id, args.name):
                return 'ok', 201
        except Exception as ex:
            print(ex)
        return 'fail', 201

    @requires_auth
    def delete(self, org_id):
        try:
            Organization.delete_by_id(org_id)
        except Exception as ex:
            print(ex)
        return 'ok', 200

# url: /api/orgs/
class OrgLists(Resource):
    def get_orgs_serialize(self):
        orgs = Organization.query.all()
        return jsonify([b.serialize for b in orgs])

    def get(self):
        return self.get_orgs_serialize()

    @requires_auth
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name')
        args = parser.parse_args()
        try:
            if args and args.name and Organization.add_new_organize(args.name):
                return 'ok', 201
        except Exception as ex:
            print(ex)
        return 'fail', 201


class LoginView(MethodView):
    """This class-based view handles contributor login and access token generation."""

    def post(self):
        """Handle POST request for this view. Url ---> /auth/login"""
        try:
            # Get the contributor object using their email (unique to every contributor)

            data = json.loads(request.data.decode())
            contributor = Adminuser.query.filter_by(
                email=data['email']).first()

            # Try to authenticate the found contributor using their password
            if contributor and contributor.password_is_valid(data['password']):
                if contributor.role != UserRole.notallowed:
                    # Generate the access token. This will be used as the authorization header
                    access_token = contributor.generate_token(contributor.id)
                    userrole = 'editor'
                    if contributor.role == UserRole.admin:
                        userrole = 'admin'
                    elif contributor.role == UserRole.editor:
                        userrole = 'editor'
                    if access_token:
                        response = {
                            'message': 'You logged in successfully.',
                            'role': userrole,
                            'token': access_token.decode()
                        }
                        return make_response(jsonify(response)), 200
                    else:
                        response = {
                            'message': 'You logged in failed.',
                        }
                    return make_response(jsonify(response)), 401

                else:
                    response = {
                        'message': 'You are not allowed to access the page.',
                    }
                    return make_response(jsonify(response)), 401
            else:
                # Contributor does not exist. Therefore, we return an error message
                response = {
                    'message': 'Invalid email or password, Please try again'
                }
                return make_response(jsonify(response)), 401

        except Exception as e:
            # Create a response containing an string error message
            response = {
                'message': str(e)
            }
            # Return a server error using the HTTP Error Code 500 (Internal Server Error)
            return make_response(jsonify(response)), 500


class RegisterView(MethodView):
    """This class-based view handles contributor login and access token generation."""

    def post(self):
        """Handle POST request for this view. Url ---> /auth/register"""
        res_msg = ''
        res_code = 501

        try:
            # Get the contributor object using their email (unique to every contributor)
            data = json.loads(request.data.decode())
            if data['email'] and data['password'] and data['name']:
                if Adminuser.add_adminuser(data):
                    res_msg = 'Success'
                else:
                    res_msg = 'Email already exists!'
                res_code = 200
            else:
                res_msg = 'Need more data!'
                res_code = 400
        except Exception as e:
            # Create a response containing an string error message
            res_msg = str(e)
            # Return a server error using the HTTP Error Code 500 (Internal Server Error)

        return make_response(jsonify({
            'message': res_msg
        })), res_code


login_view = LoginView.as_view('login_view')
register_view = RegisterView.as_view('register_view')
