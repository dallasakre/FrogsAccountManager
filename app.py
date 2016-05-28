from flask import Flask, render_template, jsonify, request, json
import cx_Oracle
from datetime import datetime
from os import environ
app = Flask(__name__)

app.config['ORACLE_SERVER'] = 'cadinfwsdpl15.corp.pvt'
app.config['ORACLE_PORT'] = 1521
app.config['ORACLE_SID'] = 'CADUPRD'
app.config['ORACLE_USER'] = 'frogs_admin'
app.config['ORACLE_PWD'] = 'apple4you'
app.config['DEBUG'] = 'TRUE'

tns_dsn = cx_Oracle.makedsn(app.config['ORACLE_SERVER'], app.config['ORACLE_PORT'], app.config['ORACLE_SID'])
conn = cx_Oracle.connect(app.config['ORACLE_USER'], app.config['ORACLE_PWD'], tns_dsn)
cur = conn.cursor()


class InvalidUsage(Exception):
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
        return rv

@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.',
        environment='Production'
    )

@app.route('/')
@app.route('/test_databases')
def test_databases():
    """Renders the test page."""
    return render_template(
        'test_databases.html',
        year=datetime.now().year,
        message='Create or Modify FROGS User Accounts in Multiple Databases for a Given Permission Level.'
    )

@app.route('/test_accounts')
def test_accounts():
    """Renders the test page."""
    return render_template(
        'test_accounts.html',
        title='Test Accounts',
        year=datetime.now().year,
        message='Your application description page.'
    )

@app.route('/test_database_role')
def test_database_role():
    """Renders the test page."""
    return render_template(
        'database_role.html',
        title='Test Database Role',
        year=datetime.now().year,
        message='Your application description page.'
    )

@app.route('/test_locked_accounts')
def test_locked_accounts():
    """Renders the test page."""
    return render_template(
        'locked_accounts.html',
        title='Test Locked Accounts',
        year=datetime.now().year,
        message='Your application description page.'
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


@app.route('/api/v1/get-frogs-database', methods=['GET'])
def frogsdatabases():
    sql = 'SELECT distinct region, database, dataset FROM frogs_user.all_datasets_and_roles order by region, database'
    data = runsql(sql)
    entries = [dict(region=row[0], database=row[1], dataset=row[2]) for row in data]
    return jsonify(frogs_databases=entries)


@app.route('/api/v1/get-frogs-locked-accounts', methods=['GET'])
def frogslockedaccount():

    def lockedusersql(db):
        sql = "SELECT '%s' as REGION, username, account_status, created, lock_date, expiry_date " \
              "FROM dba_users@%s " \
              "WHERE account_status != 'OPEN' " \
              "AND username NOT IN ('OUTLN','WMSYS','ORACLE_OCM','DIP','APPQOSSYS','DBSNMP','PERFSTAT')" % (db, db)
        return sql

    all_locked_users = {}
    sql = allfrogsdatabases()
    data = runsql(sql)
    for db in data:
        local_locked_users = []
        db = db[0]
        sql = lockedusersql(db)
        data = runsql(sql)
        for row in data:
            record = dict(database=row[0], username=row[1], status=row[2], create_date=row[3],
                          lock_date=row[4], expire_date=row[5])
            local_locked_users.append(record)
        if local_locked_users:
            all_locked_users[db] = local_locked_users
    return jsonify(frogs_locked_accounts=all_locked_users)


@app.route('/api/v1/get-all-frogs-accounts/<database>', methods=['GET'])
def frogsaccount(database):

    def usersql(sql):
        sql = "SELECT '%s' as REGION, username, created, expiry_date " \
              "FROM dba_users@%s " \
              "WHERE username NOT IN ('OUTLN','WMSYS','ORACLE_OCM','DIP','APPQOSSYS','DBSNMP','PERFSTAT'," \
              "'SYS','ORACLE','SYSTEM','SDE') AND username not like 'CADTEL%%'" % (db, db)
        return sql

    db_filter = database.upper().split(",")
    sql = allfrogsdatabases()
    data = runsql(sql)
    all_users = []
    for db in data:
        db = db[0]
        if not 'ALL' in db_filter:
            if db not in db_filter:
                continue
        sql = usersql(db)
        data = runsql(sql)
        for row in data:
            record = dict(database=row[0], username=row[1], create_date=row[2], expire_date=row[3])
            all_users.append(record)
    return jsonify(frogs_users=all_users)


@app.route('/api/v1/post-create-user', methods=['POST'])
def createuser():
    content = request.json
    failurecounter = 0
    successcounter = 0
    #expiration_date = content['expiration']
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


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
