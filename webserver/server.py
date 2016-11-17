#!/usr/bin/env python2.7

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, flash, session, url_for
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


DATABASEURI = "postgresql://ss5146:4psje@104.196.175.120/postgres"
app.secret_key = 'many random bytes'
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    return render_template("index.html")


@app.route('/index', methods = ['POST'])
def login():
    error = None
    cursor = g.conn.execute("SELECT uid FROM users")
    uids = []
    for result in cursor:
      uids.append(result['uid'])  # can also be accessed using result[0]
    cursor.close()
    
    if request.method == 'POST':
        try:
            temp_uid = int(request.form['uid'])
        except:
            error = 'Invalid User ID'
	    temp_uid = None
        if temp_uid not in uids:
            error = 'Invalid User ID'
        elif request.form['password'] != g.conn.execute('select password from users where uid = %s',temp_uid).fetchone()['password']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['uid'] = temp_uid
            flash('You were logged in')
                # return redirect('/')
    return render_template('index.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('uid',None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET','POST'])
def register_user():
    error = None
    uidresult = g.conn.execute('select max(uid)+1 as newuid from users')
    row = uidresult.fetchone()
    newuid = row['newuid']
    if request.method == 'POST':
        name = request.form['name']
	loc = request.form['location']
	dob = request.form['dob']
	email = request.form['email']
	pn = request.form['phone_number']
	pw = request.form['password']
        try:
    	    g.conn.execute("INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s)", [newuid, name, loc, dob, email, pn, pw]);
	except:
            error='Make sure you have entered a value in every field'
            return render_template('register.html',error=error)
        flash('Your unique ID is: ' + str(newuid));
        session['uid'] = newuid
    return render_template("register.html",error=error)

@app.route('/participant_register',methods=['GET','POST'])
def participant_register():
    error=None
    try:
        uid = session['uid']
    except KeyError:
        error = 'Must sign up as a generic user first'
        render_template('participant_register.html',error=error)
    try:
        if request.method == 'POST':
            height = request.form['height']
            weight = request.form['weight']
            sex = request.form['sex']
            g.conn.execute("INSERT INTO investigator VALUES (%s, %s, %s, %s)", [uid, height, weight, sex]);
    except:
        error = "Make sure you have entered something in every field"
        return render_template('participant_register.html',error=error)
    return render_template('participant_register.html',error=error)


@app.route('/investigator_register',methods=['GET','POST'])
def register_investigator():
    error=None
    try:
        uid = session['uid']
    except KeyError:
        error = 'Must sign up as a generic user first'
        render_template('investigator_register.html',error=error)
    try:
        if request.method == 'POST':
            degree = request.form['degree']
            experience = request.form['experience']
            g.conn.execute("INSERT INTO investigator VALUES (%s, %s, %s)", [uid, degree, experience]);
    except:
       error = "Make sure you have entered something in every field"
       return render_template('investigator_register.html',error=error)
    return render_template('investigator_register.html',error=error)

#@app.route('/participant')
def show_all_habit():
    cursor = g.conn.execute('select * from habit');
    habit = cursor.fetchall();
    cursor.close();
    print habit;
    return habit;
#    return render_template("participant.html", habit = habit)

#@app.route('/participant')
def show_all_medication():
    cursor = g.conn.execute('select * from medication');
    medication = cursor.fetchall();
    cursor.close();
    return medication;
#    return render_template("participant.html", medication = medication)

#@app.route('/participant')
def show_all_medical_history():
    cursor = g.conn.execute('select * from medical_history');
    medical_history = cursor.fetchall();
    cursor.close();
    return medical_history;
#    return render_template("participant.html", medical_history = medical_history)

"""
@app.route('/participant')
def show_all():
    all_habit = show_all_habit();
    all_medication = show_all_medication();
    all_medical_history = show_all_medical_history();
    return render_template("participant.html", habit = habit, medication = medication, medical_history = medical_history)
"""

@app.route('/update_height_and_weight', methods = ['GET','POST'])
def update_height_and_weight():
    if request.method == 'POST':
	try:
	    session['logged_in'] == True
        except KeyError:
            error = "You are not logged in."
            return render_template("/index.html",error=error)

	curr_uid = session['uid'];
	print(curr_uid);
	height = request.form['height'];
	weight = request.form['weight'];
        try:
	    g.conn.execute("UPDATE participant SET height = %s, weight=%s where uid = %s", [int(height), int(weight), curr_uid]);
        except:
            session['error'] = 'Please add a valid height and weight'
            return redirect('/participant')
	flash('Your height and weight were successfully updated.');
    return redirect('/participant');

def show_height_and_weight(uid):
    cursor = g.conn.execute('select height, weight from participant where uid = %s', uid);
    temp = cursor.fetchone();
    cursor.close();
    return temp.height, temp.weight

def show_habit(uid):
    cursor = g.conn.execute('select habit.hid, habit.habit_type from habit, has_habit where has_habit.hid = habit.hid and has_habit.uid = %s', uid);
    habit = cursor.fetchall();
    cursor.close();
    print habit;
    return habit

def show_medication(uid):
    cursor = g.conn.execute('select medication.mid, medication.medication_type from medication, takes where takes.mid = medication.mid and takes.uid = %s', uid);
    medication = cursor.fetchall();
    cursor.close();
    return medication

def show_medical_history(uid):
    cursor = g.conn.execute('select medical_history.mhid, medical_history.medical_history_type from medical_history, has_medical_history where has_medical_history.mhid = medical_history.mhid and has_medical_history.uid = %s', uid);
    medical_history = cursor.fetchall();
    cursor.close();
    return medical_history;

@app.route('/participant_personal')
def show():
    error = None
    try:
	session['logged_in'] == True
    except KeyError:
        error = "You are not logged in."
        return render_template("/index.html",error=error)
    uid = session['uid'];
    (height, weight) = show_height_and_weight(uid);
    habit = show_habit(uid);
    medication = show_medication(uid);
    medical_history = show_medical_history(uid);
    return render_template("participant_personal.html", height = height, weight = weight, habit = habit, medication = medication, medical_history = medical_history)

@app.route('/participant', methods = ['GET', 'POST'])
def show_select():
    try:
	session['logged_in'] == True
    except KeyError:
        error = "You are not logged in."
        return render_template("/index.html",error=error)
    all_habit = show_all_habit();
    all_medication = show_all_medication();
    all_medical_history = show_all_medical_history(); 
    uid = session['uid'];
    habit = show_habit(uid);
    medication = show_medication(uid);
    medical_history = show_medical_history(uid);
    return render_template("participant.html", all_habit = all_habit, all_medical_history = all_medical_history, all_medication = all_medication, habit = habit, medication = medication, medical_history = medical_history, error=session['error'])

@app.route('/add_habit',methods = ['GET','POST'])
def add_habit():
    hidresult = g.conn.execute('select max(hid)+1 as newhid from habit')
    row = hidresult.fetchone()
    newhid = row['newhid']
    if request.method == 'POST':
        habit_type = request.form['habit_type']
        g.conn.execute("INSERT INTO habit VALUES (%s, %s)", [newhid,habit_type]);
        flash('Your habit was successfully added')
    return render_template('add_habit.html')

@app.route('/add_medication',methods = ['GET','POST'])
def add_medication():
    midresult = g.conn.execute('select max(mid)+1 as newmid from medication')
    row = midresult.fetchone()
    newmid = row['newmid']
    if request.method == 'POST':
        medication_type = request.form['medication_type']
        g.conn.execute("INSERT INTO medication VALUES (%s, %s)", [newmid,medication_type]);
        flash('Your medication was successfully added')
    return render_template('add_medication.html')

@app.route('/add_medical_history',methods = ['GET','POST'])
def add_medical_history():
    mhidresult = g.conn.execute('select max(mhid)+1 as newmhid from medical_history')
    row = mhidresult.fetchone()
    newmhid = row['newmhid']
    if request.method == 'POST':
        medical_history_type = request.form['medical_history_type']
        g.conn.execute("INSERT INTO medical_history VALUES (%s, %s)", [newmhid,medical_history_type]);
        flash('Your medical history was successfully added')
    return render_template('add_medical_history.html')


@app.route('/get_habit',methods = ['GET','POST'])
def get_habit():
    try:
        session['logged_in'] == True
    except KeyError:
        session['error'] = "You are not logged in."
        return redirect('/participant')

    select = request.form.get('habit_select')
    g.conn.execute('DELETE FROM has_habit WHERE uid = %s AND hid = %s',[session['uid'],select])
    return redirect('/participant')

@app.route('/get_medication',methods = ['GET','POST'])
def get_medication():
    try:
        session['logged_in'] == True
    except KeyError:
        session['error'] = "You are not logged in."
        return redirect('/participant')

    select = request.form.get('medication_select')
    g.conn.execute('DELETE FROM takes WHERE uid = %s AND mid = %s',[session['uid'],select])

    return redirect('/participant')

@app.route('/get_medical_history',methods = ['GET','POST'])
def get_medical_history():
    try:
        session['logged_in'] == True
    except KeyError:
        session['error'] = "You are not logged in."
        return redirect('/participant')

    select = request.form.get('medical_history_select')
    g.conn.execute('DELETE FROM has_medical_history WHERE uid = %s AND mhid = %s',[session['uid'],select])
    return redirect('/participant')

@app.route('/get_all_habit',methods = ['GET', 'POST'])
def get_all_habit():
    try:
        session['logged_in'] = True
    except:
        error = "You are not logged in."
        return redirect("/index.html", error = error);
    select = request.form.get('all_habit_select');
    try:
	g.conn.execute('insert into has_habit values(%s, %s)', [session['uid'], select]);
    except:
	session['error'] = "You already have this habit."
	return redirect('/participant');
    return redirect('/participant')

@app.route('/get_all_medication',methods = ['GET', 'POST'])
def get_all_medication():
    try:
        session['logged_in'] = True
    except:
        error = "You are not logged in."
        return redirect("/index.html", error = error);
    select = request.form.get('all_medication_select')
    try:
	g.conn.execute('insert into takes values(%s, %s)', [select, session['uid']]);
    except:
	session['error'] = "You already take this medication."
	return redirect('/participant');
    return redirect('/participant')

@app.route('/get_all_medical_history',methods = ['GET', 'POST'])
def get_all_medical_history():
    try:
        session['logged_in'] = True
    except:
        error = "You are not logged in."
        return redirect("/index.html", error = error);
    select = request.form.get('all_medical_history_select')
    try:
	g.conn.execute('insert into has_medical_history values(%s, %s)', [select, session['uid']]);
    except:
	session['error'] = "You already have this medical history."
	return redirect('/participant');
 
    return redirect('/participant')

#@app.route('/fill_institutions',methods=['GET','POST'])
def fill_institutions():

    cursor = g.conn.execute('select iid,name from institution')
    institutions = cursor.fetchall()
    cursor.close();
    return institutions

#@app.route('/fill_grants',methods=['GET','POST'])
def fill_grants():

    cursor = g.conn.execute('select gid,name from grants')
    grants = cursor.fetchall()
    cursor.close();
    return grants
    #return render_template("manage_studies.html",grants=grants)

@app.route('/fill_inst_and_grants',methods=['GET','POST'])
def fill_inst_and_grants():
    institutions=fill_institutions()
    grants=fill_grants()
    return render_template("manage_studies.html",institution=institutions, grants=grants, error=session['error'])

@app.route('/get_institution',methods = ['POST'])
def get_institution():
    select = request.form.get('inst_select')
    session['new_study_iid'] = select
    print select
    return redirect('/manage_studies')

@app.route('/get_grant',methods = ['GET','POST'])
def get_grant():
    select = request.form.get('grant_select')
    session['new_study_gid'] = select
    print select
    return redirect('/manage_studies')

@app.route('/manage_studies',methods = ['GET','POST'])
def create_study():
    session['error']=None
    sidresult = g.conn.execute('select max(sid)+1 as newsid from study')
    row = sidresult.fetchone()
    newsid = row['newsid']
    
    if request.method == 'POST':
        try:
            session['logged_in'] == True
        except KeyError:
            session['error'] = "You are not logged in."
            return redirect('fill_inst_and_grants')
        focus = request.form['focus']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        incentive = request.form['incentive']
        risks = request.form['risks']
        cost = request.form['cost']
        no_part = request.form['no_participants']
        
        try:
            g.conn.execute("INSERT INTO study VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", [newsid, incentive, start_date, end_date, focus, no_part, risks, cost])
        except:
            session['error'] = 'Make sure you have entered a value into every field'
            return redirect('/fill_inst_and_grants')
        g.conn.execute("insert into conducts values (%s, %s)",[session['uid'],newsid])
            
        try:
            g.conn.execute("INSERT INTO funds VALUES (%s, %s)", [session['new_study_gid'], newsid])
        except:
            session['error'] = 'Something went wrong.'
            return redirect('/fill_inst_and_grants') 
        try:
            g.conn.execute("insert into oversees values (%s, %s, %s)",[session['new_study_iid'], session['new_study_gid'], newsid])
        except:
            session['error'] = 'Make sure you have selected both an institution and grant (Refresh Page)'
            return redirect('/fill_inst_and_grants')
        flash('Your study was successfully added.')
    return redirect('/fill_inst_and_grants')

@app.route('/add_institution',methods = ['GET','POST'])
def add_institution():
    error=None
    iidresult = g.conn.execute('select max(iid)+1 as newiid from institution')
    row = iidresult.fetchone()
    newiid = row['newiid']
    if request.method == 'POST':
        name = request.form['name']
        inst_type = request.form['institution_type']
        loc = request.form['location']
        if name and inst_type and loc:
            try:
                g.conn.execute("INSERT INTO institution VALUES (%s, %s, %s, %s)", [newiid,name,inst_type,loc]);
            except:
 	        error = 'Make sure you enter a value into every field'
                return render_template('add_institution.html',error=error)
        else:
            error = 'Make sure you enter a value into every field'
            return render_template('add_institution.html',error=error)
        flash('Your institution was successfully added')
    return render_template('add_institution.html', error=error)

@app.route('/add_grant',methods = ['GET','POST'])
def add_grant():
    error=None
    gidresult = g.conn.execute('select max(gid)+1 as newgid from grants')
    row = gidresult.fetchone()
    newgid = row['newgid']
    if request.method == 'POST':
        name = request.form['name']
        amount = request.form['amount']
        gtype = request.form['grant_type']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        source = request.form['source']
        if name and amount and gtype and start_date and end_date and source:
            try:
                g.conn.execute("INSERT INTO grants VALUES (%s, %s, %s, %s, %s, %s,%s)", [newgid,name,amount,gtype,start_date,end_date,source]);
            except:
                error='Make sure you have entered a value in every field'
                return render_template('add_grant.html',error=error)
        else:
            error='Make sure you have entered a value in every field'
            return render_template('add_grant.html',error=error)
        flash('Your grant was successfully added')
    return render_template('add_grant.html',error=error)

@app.route('/search_participants',methods = ['GET','POST'])
def search_participants():

    uids = []
    
    if request.method == 'POST':
        loc = request.form['location']
        sex = request.form['sex']
        habit = request.form['habit']
        medication = request.form['medication']
        med_history = request.form['med_history']

        #set of all possible participants
        participants = g.conn.execute("SELECT uid FROM participant")
        for p in participants:
            uids.append(p['uid'])

        if loc:
            temp_uids = []
            query = "SELECT uid FROM users WHERE location LIKE LOWER(%s)"
            match = g.conn.execute(query, '%' + loc.lower() + '%')
            for p in match:
                temp_uids.append(p['uid'])
            uids = list(set(uids) & set(temp_uids))
        if habit:
            temp_uids = []
            query = "SELECT has_habit.uid FROM has_habit,habit WHERE habit_type LIKE LOWER(%s) and habit.hid = has_habit.hid"
            match = g.conn.execute(query, '%' + habit.lower() + '%')
            for p in match:
                temp_uids.append(p['uid'])
            uids = list(set(uids) & set(temp_uids))
        if medication:
            temp_uids = []
            query = "SELECT takes.uid FROM takes, medication WHERE medication_type LIKE LOWER(%s) and medication.mid = takes.mid"
            match = g.conn.execute(query, '%' + medication.lower() + '%')
            for p in match:
                temp_uids.append(p['uid'])
            uids = list(set(uids) & set(temp_uids))
        if med_history:
            temp_uids = []
            query = "SELECT has_medical_history.uid FROM has_medical_history,medical_history WHERE medical_history_type LIKE LOWER(%s) and medical_history.mhid = has_medical_history.mhid"
            match = g.conn.execute(query, '%' + med_history.lower() + '%')
            for p in match:
                temp_uids.append(p['uid'])
            uids = list(set(uids) & set(temp_uids))
        if sex:
            temp_uids = []
            match = g.conn.execute("SELECT uid FROM participant WHERE sex = LOWER(%s)",sex.lower())
            for p in match:
                temp_uids.append(p['uid'])
            uids = list(set(uids) & set(temp_uids))
    placeholder= '%s'
    placeholders= ', '.join(placeholder for unused in uids)
    
    query= 'SELECT name, email FROM users WHERE uid IN (%s)' % placeholders
    try:
        cursor= g.conn.execute(query, uids)
    except:
        cursor = []
        pass
    search_results = []
    for row in cursor:
        search_results.append(row['name'] + ', ' + row['email'])
    return render_template("search_participants.html", search_results=search_results)

@app.route('/search_study',methods = ['GET','POST'])
def search_study():

    sids = []

    if request.method == 'POST':
        loc = request.form['location']
        focus = request.form['focus']
        #set of all possible studies
        studies = g.conn.execute("SELECT sid FROM study")
        for s in studies:
            sids.append(s['sid'])

        if loc:
            temp_sids = []
            query = "select oversees.sid from oversees, institution where oversees.iid=institution.iid and institution.location LIKE LOWER(%s)"
            match = g.conn.execute(query, '%' + loc.lower() + '%')
            for s in match:
                temp_sids.append(s['sid'])
            sids = list(set(sids) & set(temp_sids))

        if focus:
            temp_sids = []
            query = "SELECT sid FROM study WHERE study.focus LIKE LOWER(%s)"
            match = g.conn.execute(query, '%' + focus.lower() + '%')
            for s in match:
                temp_sids.append(s['sid'])
            sids = list(set(sids) & set(temp_sids))

    placeholder= '%s'
    placeholders= ', '.join(placeholder for unused in sids)
    
    query= 'SELECT incentives, focus, start_date, end_date FROM study WHERE sid IN (%s)' % placeholders
    try:
        cursor= g.conn.execute(query, sids)
    except:
        cursor = []
        pass
    search_results = []
    for row in cursor:
        search_results.append(row['incentives'] + ', ' + row['focus'] + ', ' + str(row['start_date']) + ', ' + str(row['end_date']))
 
    return render_template("search_study.html", search_results=search_results)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
