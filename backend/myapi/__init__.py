from jinja2 import TemplateNotFound
from flask import Blueprint, render_template, abort, jsonify
from flask import Flask, request, make_response
from flask_restful import Resource, Api
from myapi.models import Adminuser
import jwt
import datetime
from myapi.resources import (UserDetails, UserLists, OrgDetails, OrgLists, CSVImports, login_view,
                             AdminManage, register_view, AdminUserManage, AdminUserList, UserManageLists)


def create_api():
    api = Api(api_resource)
    # User side Rest API
    api.add_resource(UserDetails, '/users/<string:user_id>')
    api.add_resource(UserLists, '/users/')
    api.add_resource(OrgDetails, '/orgs/<string:org_id>')
    # Admin Side Rest API org
    api.add_resource(OrgLists, '/orgs/')
    # Upload csv
    api.add_resource(CSVImports, '/csv/')
    # update password
    api.add_resource(AdminManage, '/admin/')
    # user pendding and update list
    api.add_resource(UserManageLists, '/admin/usersmanage/')
    # edit editors and admin
    api.add_resource(AdminUserList, '/admin/users/')
    # admin update detail information
    api.add_resource(AdminUserManage, '/admin/users/<string:user_id>/')

    # login user
    api_resource.add_url_rule(
        '/auth/login/',
        view_func=login_view,
        methods=['POST']
    )
    # register user
    api_resource.add_url_rule(
        '/auth/register/',
        view_func=register_view,
        methods=['POST']
    )


# leading '/api' REST API creation
api_resource = Blueprint('api', __name__, url_prefix='/api')
create_api()
