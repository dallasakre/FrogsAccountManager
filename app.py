from flask import Flask, render_template, jsonify, request, url_for, redirect, flash, g
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user
from functools import wraps
import cx_Oracle
import ldap
from datetime import datetime
from os import environ
app = Flask(__name__)

app.config['SECRET_KEY'] = '03{gUGLFnBD+5C=oS%WP0@GL6E54#W'

app.config['ORACLE_SERVER'] = 'cadinfwsdpl15.corp.pvt'
app.config['ORACLE_PORT'] = 1521
app.config['ORACLE_SID'] = 'CADUPRD'
app.config['ORACLE_USER'] = 'frogs_admin'
app.config['ORACLE_PWD'] = 'apple4you'
app.config['DEBUG'] = 'TRUE'
app.config['USER_GROUPS'] = ['ENG_SYS_APPS_POWERUSERS', 'ENG_SYS_APPS_ADMINS', 'ENG_SYS_APPS', 'NYRO_CITRIX_HELPDESK']



login_manager = LoginManager()
login_manager.session_protection = 'strong'
users = {}
login_manager.view = 'login'
login_manager.init_app(app)


tns_dsn = cx_Oracle.makedsn(app.config['ORACLE_SERVER'], app.config['ORACLE_PORT'], app.config['ORACLE_SID'])
conn = cx_Oracle.connect(app.config['ORACLE_USER'], app.config['ORACLE_PWD'], tns_dsn)
cur = conn.cursor()


# Declare an Object Model for the user, and make it comply with the
# flask-login UserMixin mixin.
class User(UserMixin):
    def __init__(self, username, ldap_login_id, group_memebership, display_name):
        self.ldap_login_id = ldap_login_id
        self.username = username
        self.group_memebership = group_memebership
        self.display_name = display_name

    def __repr__(self):
        return self.username

    def get_id(self):
        return self.username

    def is_anonymous(self):
        return False


# Declare a User Loader for Flask-Login.
# Simply returns the User if it exists in our 'database', otherwise
# returns None.
@login_manager.user_loader
def load_user(id):
    if id in users:
        return users[id]
    return None


# Declare The User Saver for Flask-Ldap3-Login
# This method is called whenever a LDAPLoginForm() successfully validates.
# Here you have to save the user, and return it so it can be used in the
# login controller.

def save_user(username, ldap_login_id, membership, display_name):
    user = User(username, ldap_login_id, membership, display_name)
    users[username] = user
    login_user(user)
    return user


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def get_current_user():
    g.user = current_user


""""class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv"""""


@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    next = request.args.get('next')
    if request.method == 'GET':
        if current_user.is_authenticated:
            flash('You are already logged in.')
            redirect(url_for('lookup_accounts'))
        else:
            return render_template('login.html',
                                   title='Login',
                                   year=datetime.now().year,
                                   message='Login to the FROGS Account Manager.',
                                   next=next)


    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        ldap_login_id = username + '@ftr.com'
        next = request.form['next']

        try:
            l = ldap.initialize("ldap://ldaphost.corp.pvt")
            l.protocol_version = ldap.VERSION3
            l.set_option(ldap.OPT_REFERRALS, 0)
            l.simple_bind_s(ldap_login_id, password)
        except ldap.INVALID_CREDENTIALS:
            flash('Invalid username or password.  Please try again.', 'danger')
            return redirect(url_for('login'))
        try:
            filter = "(&(objectClass=person)(samaccountname=%s))" % username
            results = l.search_s("dc=corp,dc=pvt",ldap.SCOPE_SUBTREE,filter,['displayName','memberOf'])
        except Exception, e:
            search_error = str(e)
            flash('An error has occurred! Error: ' + search_error, 'danger')
            return redirect(url_for('login'))
        try:
            for entry in results:
                if entry[0] is not None:
                    groups = entry[1]['memberOf']
                    display_name = entry[1]['displayName'][0]

            for group in ['ENG_SYS_APPS_POWERUSERS', 'ENG_SYS_APPS_ADMINS', 'ENG_SYS_APPS', 'NYRO_CITRIX_HELPDESK']:
                if any(group in s for s in groups):
                    save_user(username, ldap_login_id, group, display_name)
                    if not next == 'None':
                        return redirect(next)
                    else:
                        return redirect(url_for('lookup_accounts'))
            flash('You do not have proper permissions to view additional options.', 'danger')
            return redirect(url_for('login'))
        except Exception, e:
            search_error = str(e)
            flash('An error has occurred! Error: ' + search_error, 'danger')
            return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/create_user')
@login_required
def create_user():
    return render_template(
        'create_user.html',
        title='Create/Modify Users',
        year=datetime.now().year,
        message='Create or Modify FROGS User Accounts in Multiple Databases for a Given Permission Level.'
    )


@app.route('/lookup_accounts')
def lookup_accounts():
    return render_template(
        'lookup_accounts.html',
        title='Lookup/Export Accounts',
        year=datetime.now().year,
        message='Lookup and Export FROGS User Information.'
    )


@app.route('/remove_accounts')
@login_required
def remove_accounts():
    return render_template(
        'remove_accounts.html',
        title='Remove Accounts',
        year=datetime.now().year,
        message='Remove users from FROGS Databases.'
    )


@app.route('/locked_accounts')
@login_required
def locked_accounts():
    return render_template(
        'locked_accounts.html',
        title='Locked Accounts',
        year=datetime.now().year,
        message='Unlock FROGS User Accounts.'
    )


@app.route('/api/v1/get-frogs-dataset-role/<database>', methods=['GET'])
def frogsdatasetsroles(database):
    if database.lower() == 'all':
        sql = "SELECT * FROM frogs_user.all_datasets_and_roles"
    else:
        sql = "SELECT * FROM frogs_user.all_datasets_and_roles WHERE database IN ('%s')" \
              % database.replace(",", "','").upper()
    data = runsql(sql)
    entries = [dict(region=row[0], database=row[1], schema=row[2], dataset=row[3], role=row[4]) for row in data]
    return jsonify(frogs_datasets_roles=entries)


@app.route('/api/v1/get-frogs-database-dataset', methods=['GET'])
def frogsdatabasedataset():
    sql = 'SELECT distinct region, database, dataset FROM frogs_user.all_datasets_and_roles order by region, database'
    data = runsql(sql)
    entries = [dict(region=row[0], database=row[1], dataset=row[2]) for row in data]
    return jsonify(frogs_databases=entries)


@app.route('/api/v1/get-frogs-database', methods=['GET'])
def frogsdatabase():
    sql = 'SELECT distinct region, database FROM frogs_user.all_datasets_and_roles order by region, database'
    data = runsql(sql)
    entries = [dict(region=row[0], database=row[1]) for row in data]
    return jsonify(frogs_databases=entries)


@app.route('/api/v1/get-frogs-locked-accounts', methods=['GET'])
def frogslockedaccount():

    def lockedusersql(db):
        sql = "SELECT '%s' as REGION, username, account_status, created, lock_date, expiry_date " \
              "FROM dba_users@%s " \
              "WHERE account_status != 'OPEN' " \
              "AND username NOT IN ('OUTLN','WMSYS','ORACLE_OCM','DIP','APPQOSSYS','DBSNMP','PERFSTAT'," \
              "'ANONYMOUS','CTXSYS','EXFSYS','IGNITEREP','LBACSYS','MDDATA','MDSYS','MGMT_VIEW','OLAPSYS'," \
              "'ORACLE_OCM','ORDPLUGINS','ORDSYS','OWBSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSMAN'," \
              "'SYSTEM','TSMSYS','VZDBMON','VZDBMONX','WK_TEST','WKPROXY','WKSYS','WMSYS','XDB')" % (db, db)
        return sql

    locked_users = []
    sql = allfrogsdatabases()
    data = runsql(sql)
    for db in data:
        db = db[0]
        sql = lockedusersql(db)
        data = runsql(sql)
        for row in data:
            record = dict(database=row[0], username=row[1], status=row[2], create_date=row[3],
                          lock_date=row[4], expire_date=row[5])
            locked_users.append(record)
    return jsonify(frogs_locked_accounts=locked_users)


@app.route('/api/v1/post-all-frogs-accounts', methods=['POST'])
def frogsaccount():
    content = request.json
    databases = content['databases']
    dbInStatement = " AND database IN ('" + "','".join(map(str, databases)).upper() + "') "
    users = content['users']
    userInStatement = " AND grantee IN ('" + "','".join(map(str, users)).upper() + "') "

    sql = "SELECT grantee, region, database, dataset, role " \
          "FROM FROGS_ACCT_MGR_USER_ROLE " \
          "WHERE grantee NOT IN ('OUTLN','WMSYS','ORACLE_OCM','DIP','APPQOSSYS','DBSNMP','PERFSTAT'," \
          "'ANONYMOUS','CTXSYS','EXFSYS','IGNITEREP','LBACSYS','MDDATA','MDSYS','MGMT_VIEW','OLAPSYS'," \
          "'ORACLE_OCM','ORDPLUGINS','ORDSYS','OWBSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSMAN'," \
          "'SYSTEM','TSMSYS','VZDBMON','VZDBMONX','WK_TEST','WKPROXY','WKSYS','WMSYS','XDB')" \
          "AND grantee not like 'CADTEL%%'"

    if databases:
        sql = sql + dbInStatement

    if users:
        sql = sql + userInStatement
    try:
        data = runsql(sql)
        users = []
        for row in data:
            record = dict(username=row[0], region=row[1], database=row[2], dataset=row[3], role=row[4])
            users.append(record)
        return jsonify(frogs_users=users)
    except Exception, e:
        return jsonify(oracle_error=str(e))


@app.route('/api/v1/post-unlock-frogs-user', methods=['POST'])
def unlockuser():
    failurecounter = 0
    successcounter = 0
    failures = []
    content = request.json
    locked_accounts = content['frogs_locked_accounts']
    for row in locked_accounts:
        user = row['account']
        db = row['database']
        try:
            result, oraerror = unlockfrogsaccount(user, db)
            status = result[2]
            message = result[3]
            if not oraerror:
                if status != 'SUCCESS':
                    failurecounter = failurecounter + 1
                    failrecord = dict(username=user, database=db, status=status, message=message)
                    failures.append(failrecord)
                else:
                    successcounter = successcounter + 1
            else:
                return jsonify(oracle_error=oraerror)
        except Exception as ex:
            failurecounter = failurecounter + 1
            failrecord = dict(username=user, database=db, status="Oracle Error", message=str(ex))
            failures.append(failrecord)

    response = dict(success_counter=successcounter,failure_counter=failurecounter,failure_details=failures)
    return jsonify(response)


@app.route('/api/v1/post-create-user', methods=['POST'])
def createuser():
    content = request.json
    failurecounter = 0
    successcounter = 0
    permission_level = content['permission']
    database_dataset = content['database_dataset']
    usernames = content['users']
    dicDbDs = {}

    for val in database_dataset:
        val = val.split('-')
        db = val[0]
        ds = val[1]
        if not db in dicDbDs.keys():
            aryDs = []
            aryDs.append(ds)
            dicDbDs[db] = aryDs
        else:
            aryDs = []
            aryDs = dicDbDs[db]
            aryDs.append(ds)
            dicDbDs[db] = aryDs

    failures = []
    for database, datasets in dicDbDs.iteritems():
        for username in usernames:
            try:
                result, oraerror = createuseraddrole(username, database, permission_level, datasets)
                status = result[4]
                message = result[5]
                if not oraerror:
                    if status != 'SUCCESS':
                        failurecounter = failurecounter + 1
                        failrecord = dict(username=username, database=database, status=status, message=message)
                        failures.append(failrecord)
                    else:
                        successcounter = successcounter + 1
                else:
                    return jsonify(oracle_error=oraerror)
            except Exception as ex:
                return jsonify(python_error=ex.message)
    response = dict(success_counter=successcounter,failure_counter=failurecounter,failure_details=failures)
    return jsonify(response)


def runsql(sql):
    cur.execute(sql)
    data = cur.fetchall()
    return data


def allfrogsdatabases():
    sql = "SELECT db_link from dba_db_links WHERE username = 'CADTEL_ADMIN_LOGIC6' AND db_link LIKE '%PRD'"
    return sql


def createuseraddrole(user, db, role, datasets):
    error = []
    try:
        oraArrayDatasets = cur.arrayvar(cx_Oracle.STRING, datasets)
        oraStatus = cur.var(cx_Oracle.STRING)
        oraMsg = cur.var(cx_Oracle.STRING)
        results = cur.callproc("FROGS_ACCT_MGR.CREATE_FROGS_USER_ADD_ROLE", (user, db, role, oraArrayDatasets, oraStatus, oraMsg))
        return results, error
    except cx_Oracle.DatabaseError as ex:
        error = ex.args
    return results, error


def unlockfrogsaccount(user, db):
    error = []
    try:
        database = db
        account = user
        oraStatus = cur.var(cx_Oracle.STRING)
        oraMsg = cur.var(cx_Oracle.STRING)
        results = cur.callproc("FROGS_ACCT_MGR.UNLOCK_FROGS_USER", (account, database, oraStatus, oraMsg))
        return results, error
    except cx_Oracle.DatabaseError as ex:
        error = ex.args
    return error

"""
@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response"""


if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
