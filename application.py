#!/usr/bin/env python3

from flask import Flask, session, \
    render_template, jsonify, request, redirect, url_for, flash, make_response
from sqlalchemy import create_engine
from functools import wraps
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem, User
from flask import session as login_session
import requests
import httplib2
import random
import re
import string
import json
from sendOtp import sendotp

otpauth = sendotp()
app = Flask(__name__)
senderId = "Wedyne"
# Connect to Database and create database session
engine = create_engine('sqlite:///restaurantmenuwithusers.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    @wraps(f)
    def x(*args, **kwargs):
        if 'email' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return x


def check_user(f):
    @wraps(f)
    def x(restaurant_id):
        restaurants = session.query(Restaurant).get(restaurant_id)
        if login_session['email'] != restaurants.user.email:
            return "permission denied"
        else:
            return f(restaurant_id)
    return x


def redirect_url(default='showCatalogs'):
    return request.args.get('next') or \
        request.referrer or \
        url_for(default)


# JSON APIs to view Restaurant Information
@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id=menu_id).one_or_none()
    return jsonify(Menu_Item=Menu_Item.serialize)


@app.route('/JSON/')
@app.route('/restaurants/JSON/')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])


# Show all restaurants
@app.route('/')
@app.route('/restaurants/')
def showCatalogs():
    restaurants = session.query(Restaurant).all()
    items = session.query(MenuItem).order_by(MenuItem.id.desc()).limit(5)
    return render_template('publicrestaurants.html',
                           restaurants=restaurants, items=items)


@app.route('/restaurants/<int:restaurant_id>/')
@app.route('/restaurants/<int:restaurant_id>/<path:restaurant_name>/')
def showRestaurantsItem(restaurant_name, restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    restaurants = session.query(Restaurant).all()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant.id).order_by(MenuItem.id.desc())
    quantity = items.count()
    return render_template('restaurantsmenu.html',
                           restaurants=restaurants,
                           items=items, restaurant=restaurant,
                           quantity=quantity)


@app.route('/restaurants/<int:restaurant_id>/'
           '<path:restaurant_name>/<int:menu_id>/')
@app.route('/restaurants/<int:restaurant_id>/'
           '<path:restaurant_name>/<int:menu_id>/<path:menu_name>/')
def showMenuItems(restaurant_id, menu_id, restaurant_name, menu_name):
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    return render_template('restaurantmenuitem.html', item=item)


# Task 1: Create route for newMenuItem function here

@app.route('/restaurants/<int:user_id>/info')
def showUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return render_template('userinfo.html', user=user)


@login_required
@app.route('/restaurants/category/new/', methods=['GET', 'POST'])
def newCategory():
    if request.method == 'POST':
        newcategory = Restaurant(name=request.form['name'],
                                 user_id=login_session['user_id'])
        session.add(newcategory)
        session.commit()
        flash("new Category %s created!" % request.form['name'])
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('newCategory.html')


@login_required
@app.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
@check_user
def editCategory(restaurant_id):
    editedRestaurant = session.query(Restaurant) \
        .filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedRestaurant.name = request.form['name']
            flash("Category %s has been edited" % request.form['name'])
            return redirect(url_for('showCatalogs'))
    else:
        return render_template('editCategory.html',
                               restaurant=editedRestaurant)


@login_required
@app.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
@check_user
def deleteCategory(restaurant_id):
    deleteRestaurant = session.query(Restaurant) \
        .filter_by(id=restaurant_id).one_or_none()
    itemToDelete = session.query(MenuItem) \
        .filter_by(restaurant_id=restaurant_id).delete()
    if request.method == 'POST':
        session.delete(deleteRestaurant)
        session.commit()
        flash("Category has been deleted")
        return redirect(
            url_for('showCatalogs'))
    else:
        return render_template('deleteCategory.html',
                               restaurant=deleteRestaurant)


@login_required
@app.route('/restaurant/<int:restaurant_id>/'
           'menu/new/', methods=['GET', 'POST'])
@check_user
def newMenuItem(restaurant_id):
    if request.method == 'POST':
        newItem = MenuItem(name=request.form['name'],
                           description=request.form['description'],
                           price=request.form['price'],
                           course=request.form['course'],
                           picture=request.form['picture'],
                           restaurant_id=restaurant_id,
                           user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash(f"New Item {request.form['name']} has been created")
        return redirect(url_for('showCatalogs'))
    else:
        restaurants = session.query(Restaurant).all()
        return render_template('newmenuitem.html', restaurants=restaurants)


# Task 2: Create route for editMenuItem function here
@check_user
@login_required
@app.route('/restaurants/<int:restaurant_id>/'
           'menu/<int:menu_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['course']:
            editedItem.course = request.form['course']
        if request.form['picture']:
            editedItem.course = request.form['picture']
        if login_session['user_id']:
            editedItem.user_id = login_session['user_id']
        session.add(editedItem)
        session.commit()
        flash("Item %s has been updated" % request.form['name'])
        return redirect(url_for('showCatalogs'))
    else:

        return render_template('editmenuitem.html',
                               restaurant_id=restaurant_id,
                               menu_id=menu_id, item=editedItem)


# Task 3: Create a route for deleteMenuItem function here
@login_required
@app.route("/restaurants/<int:restaurant_id>/"
           "menu/<int:menu_id>/delete/", methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Item has been deleted")
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('deleteMenuItem.html', item=itemToDelete)


# TODO Limit the number of false request (brute force prevention)
@app.route("/verification", methods=['GET', 'POST'])
def verification():
    if 'mob_no' not in login_session:
        flash('Invalid Url')
        return redirect(redirect_url())
    if request.method == 'POST':
        cc = login_session.get('countrycode')
        mob = login_session['mob_no']
        phone = '+' + cc + mob
        otp = request.form['otp']
        status = otpauth.verify(contactNumber=phone, otp=otp)
        j_status = json.loads(status)
        if j_status["type"] == 'success':
            if 'type' in login_session:
                if login_session['type'] == 'A':
                    user = session.query(User).filter_by(
                        mob_no=login_session['mob_no']).first()
                    # log user in
                    login_session['name'] = user.name
                    login_session['email'] = user.email
                    flash('You are now logged in!')
                    return redirect(url_for('showCatalogs'))
                if login_session['type'] == 'B':
                    # log user in
                    create_user(login_session)
                    login_session.clear()
                    flash('You are successfully Registered!')
                    # flash(ver['messages'])
                    return redirect(url_for('login'))
            flash("Invalid request.")
            return redirect(url_for('login'))
        flash(j_status['message'])
        return redirect(url_for('verification'))
    return render_template('verification.html')


def create_user(login_session):
    newUser = User(name=login_session['name'], code=login_session['countrycode'],
                   mob_no=login_session['mob_no'], email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(mob_no=login_session['mob_no']).one()
    return user.id


@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'email' in login_session:
        flash('you are already logged in')
        return redirect(url_for('showCatalogs'))
    if request.method == 'POST':
        countrycode = request.form['countryCode']
        mob_no = request.form['mob_no']
        pattern = r"^[6789]{1}\d{9}$"
        if not re.match(pattern, mob_no):
            flash(f'Mobile Number {mob_no} not validate')
            return redirect(url_for('login'))
        phone = '+' + countrycode + mob_no
        user = session.query(User).filter_by(mob_no=mob_no).first()
        if user is None:
            flash(f'Mobile Number {mob_no} is not registerd', 'error')
            return redirect(url_for('register'))
        otpauth.send(contactNumber=phone, senderId=senderId)
        login_session['type'] = 'A'
        login_session['countrycode'] = countrycode
        login_session['mob_no'] = mob_no
        flash(f'otp is sent to {mob_no}.')
        return redirect(url_for('verification'))
    return render_template('login.html')

# Create anti-forgery state token
@app.route("/register", methods=['GET', 'POST'])
def register():
    if 'email' in login_session:
        flash('you are already logged in')
        return redirect(url_for('showCatalogs'))
    if request.method == 'POST':
        name = request.form['name']
        countrycode = request.form['countryCode']
        mob_no = request.form['mob_no']
        email = request.form['email']
        m_pattern = r"^[6789]{1}\d{9}$"
        e_pattern = r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        if not re.match(m_pattern, mob_no):
            flash(f'Mobile Number {mob_no} not validate')
            return redirect(url_for('register'))
        if not re.match(e_pattern, email):
            flash(f'Mobile Number {email} not validate')
            return redirect(url_for('register'))
        phone = '+' + countrycode + mob_no
        user = session.query(User).filter_by(mob_no=mob_no).first()
        if user is not None:
            flash(f'Mobile Number {mob_no} already registerd', 'error')
            return redirect(url_for('login'))
        otpauth.send(contactNumber=phone, senderId=senderId)
        login_session['type'] = 'B'
        login_session['mob_no'] = mob_no
        login_session['name'] = name
        login_session['countrycode'] = countrycode
        login_session['email'] = email
        flash(f'otp is sent to {mob_no}.')
        return redirect(url_for('verification'))
    else:
        return render_template('login.html')


@login_required
@app.route('/logout')
def logout():
    del login_session['name']
    del login_session['mob_no']
    del login_session['email']
    del login_session['countrycode']
    flash('successfully Logout')
    return redirect(url_for('login'))


# This only happens when project.py is called directly:
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='localhost', port=5000)
